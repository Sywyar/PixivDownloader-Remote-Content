from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import renew_announcements as renewer
import validate_content as validator


class AnnouncementRenewalTest(unittest.TestCase):
    def setUp(self):
        self.index = validator.load_index_bytes(validator.INDEX_PATH.read_bytes(), "index.json")
        self.expires = validator.utc_timestamp(self.index["expiresAt"], "expiresAt")

    def test_renewal_starts_at_seven_days_and_recovers_expired_indexes(self):
        boundary = self.expires - timedelta(days=7)
        self.assertIsNone(renewer.renewal(self.index, boundary - timedelta(microseconds=1)))
        for now in (boundary, self.expires, self.expires + timedelta(days=100)):
            with self.subTest(now=now):
                candidate = renewer.renewal(self.index, now)
                self.assertEqual(self.index["sequence"] + 1, candidate["sequence"])
                self.assertEqual(now, validator.utc_timestamp(candidate["generatedAt"], "generatedAt"))
                self.assertEqual(now + timedelta(days=30), validator.utc_timestamp(candidate["expiresAt"], "expiresAt"))
                self.assertEqual({k: v for k, v in self.index.items() if k not in {"sequence", "generatedAt", "expiresAt"}},
                                 {k: v for k, v in candidate.items() if k not in {"sequence", "generatedAt", "expiresAt"}})
                validator.validate_index(candidate)
                self.assertIsNone(renewer.renewal(candidate, now))

    def test_invalid_sequence_time_and_future_clock_are_rejected(self):
        for key, value in (("sequence", True), ("sequence", 0), ("sequence", 2**63 - 1),
                           ("generatedAt", "invalid"), ("expiresAt", self.index["generatedAt"]),
                           ("generatedAt", (self.expires + timedelta(days=1)).isoformat().replace("+00:00", "Z"))):
            with self.subTest(key=key, value=value):
                candidate = {**self.index, key: value}
                with self.assertRaises(validator.ValidationError):
                    renewer.renewal(candidate, self.expires)
        generated = validator.utc_timestamp(self.index["generatedAt"], "generatedAt")
        with self.assertRaises(validator.ValidationError):
            renewer.renewal(self.index, generated - timedelta(minutes=10, seconds=1))

    def test_cli_check_preserves_bytes_and_write_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "index.json"
            output = Path(directory) / "output"
            original = copy.deepcopy(self.index)
            original.update(generatedAt="2020-01-01T00:00:00Z", expiresAt="2020-01-31T00:00:00Z")
            data = json.dumps(original, ensure_ascii=False).encode("utf-8")
            index.write_bytes(data)
            with patch.object(renewer, "INDEX_PATH", index):
                with patch.object(sys, "argv", ["renew", "--github-output", str(output)]):
                    self.assertEqual(0, renewer.main())
                self.assertEqual(data, index.read_bytes())
                self.assertEqual("due=true\n", output.read_text(encoding="utf-8"))
                with patch.object(sys, "argv", ["renew", "--write"]):
                    self.assertEqual(0, renewer.main())
                    renewed = index.read_bytes()
                    self.assertNotEqual(data, renewed)
                    self.assertEqual(0, renewer.main())
                    self.assertEqual(renewed, index.read_bytes())
                candidate = validator.load_index_bytes(renewed, "renewed")
                self.assertEqual(original["announcements"], candidate["announcements"])
                self.assertEqual(original["sequence"] + 1, candidate["sequence"])
                validator.validate_index(candidate)

    @unittest.skipUnless(os.environ.get("SIGNATURE_TOOL_JAR"), "Set SIGNATURE_TOOL_JAR for the real signature round-trip")
    def test_real_signer_preserves_the_signature_protocol_and_rejects_tampering(self):
        tool = ["java", "-cp", str(Path(os.environ["SIGNATURE_TOOL_JAR"]).resolve()),
                "top.sywyar.pixivdownload.plugin.signature.cli.PluginSignatureTool"]

        def run(*args, accepted=True):
            result = subprocess.run([*tool, *args], capture_output=True, text=True, check=False)
            self.assertEqual(accepted, result.returncode == 0, result.stdout + result.stderr)

        run("verify-manifest", "--manifest", str(validator.INDEX_PATH), "--signature", str(validator.SIGNATURE_PATH),
            "--repository-id", "pixivdownloader-remote-announcements")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generator = root / "TestKey.java"
            generator.write_text('''import java.nio.file.*;
import java.security.*;
import java.util.Base64;
class TestKey {
    public static void main(String[] args) throws Exception {
        var pair = KeyPairGenerator.getInstance("Ed25519").generateKeyPair();
        Files.writeString(Path.of(args[0], "private.pem"), "-----BEGIN PRIVATE KEY-----\\n"
            + Base64.getEncoder().encodeToString(pair.getPrivate().getEncoded()) + "\\n-----END PRIVATE KEY-----\\n");
        Files.writeString(Path.of(args[0], "public.txt"), Base64.getEncoder().encodeToString(pair.getPublic().getEncoded()));
    }
}
''', encoding="utf-8")
            subprocess.run(["java", str(generator), str(root)], check=True, capture_output=True)
            manifest, signature = root / "index.json", root / "index.json.sig"
            candidate = renewer.renewal(self.index, self.expires)
            manifest.write_bytes((json.dumps(candidate, ensure_ascii=False) + "\n").encode("utf-8"))
            run("manifest", "--manifest", str(manifest), "--repository-id", "pixivdownloader-remote-announcements",
                "--key-id", "renewal-test", "--private-key", str(root / "private.pem"), "--out", str(signature))
            verify = ["verify-manifest", "--manifest", str(manifest), "--signature", str(signature),
                      "--repository-id", "pixivdownloader-remote-announcements"]
            run(*verify, accepted=False)
            trust = ["--policy", "custom", "--trusted-key-id", "renewal-test",
                     "--trusted-public-key", (root / "public.txt").read_text(encoding="utf-8")]
            run(*verify, *trust)
            manifest.write_bytes(manifest.read_bytes() + b" ")
            run(*verify, *trust, accepted=False)


if __name__ == "__main__":
    unittest.main()
