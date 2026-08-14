from pathlib import Path
import copy
import unittest

import validate_content as validator


DOCUMENT = (Path(__file__).parents[1]
            / "announcements" / "welcome-2026-08-12" / "en-US.html").read_text(encoding="utf-8")
TITLE = "Welcome to PixivDownloader"


def validate(source: str) -> None:
    parser = validator.AnnouncementParser(validator.ROOT / "fixture.html", "en-US", TITLE)
    parser.feed(source)
    parser.close_and_validate()


class ContentValidatorTest(unittest.TestCase):
    def current_index(self):
        return validator.load_index_bytes(validator.INDEX_PATH.read_bytes(), "index.json")

    def test_current_document_is_accepted(self):
        validate(DOCUMENT)
        validator.validate_index(self.current_index())
        signature = validator.load_index_bytes(
            validator.SIGNATURE_PATH.read_bytes(), "index.json.sig")
        validator.validate_signature(signature)

    def test_active_or_external_content_is_rejected(self):
        attacks = (
            DOCUMENT.replace("</body>", "<script>alert(1)</script></body>"),
            DOCUMENT.replace("<main>", '<main onclick="alert(1)">'),
            DOCUMENT.replace("</body>", "<iframe srcdoc=x></iframe></body>"),
            DOCUMENT.replace("body {", "body { background-image: url(https://evil.example/x);"),
            DOCUMENT.replace("body {", "body { background-image: linear-gradient(red, blue);"),
            DOCUMENT.replace("https://github.com/Sywyar/PixivDownloader",
                             "https://evil.example/PixivDownloader", 1),
            DOCUMENT.replace("<body>", "<?xml version='1.0'?><body>"),
        )
        for source in attacks:
            with self.subTest(source=source[-100:]):
                with self.assertRaises(validator.ValidationError):
                    validate(source)

    def test_security_policy_is_required_verbatim(self):
        with self.assertRaises(validator.ValidationError):
            validate(DOCUMENT.replace("script-src 'none'; ", "", 1))

    def test_only_indexed_html_is_allowed(self):
        original_listing = validator.listed_repository_files
        validator.listed_repository_files = lambda: original_listing() | {Path("outside.html")}
        try:
            with self.assertRaises(validator.ValidationError):
                validator.validate_index(
                    validator.load_index_bytes(validator.INDEX_PATH.read_bytes(), "index.json"))
        finally:
            validator.listed_repository_files = original_listing

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(validator.ValidationError):
            validator.load_index_bytes(b'{"schemaVersion":1,"schemaVersion":1}', "fixture")

    def test_index_sequence_validity_and_document_digest_are_required(self):
        mutations = []
        for key, value in (("sequence", 0),
                           ("expiresAt", "2026-10-01T15:00:00Z")):
            candidate = copy.deepcopy(self.current_index())
            candidate[key] = value
            mutations.append(candidate)
        candidate = copy.deepcopy(self.current_index())
        candidate["announcements"][0]["locales"]["en-US"]["contentSha256"] = "0" * 64
        mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                with self.assertRaises(validator.ValidationError):
                    validator.validate_index(candidate)

    def test_signature_metadata_is_strict(self):
        signature = validator.load_index_bytes(
            validator.SIGNATURE_PATH.read_bytes(), "index.json.sig")
        for key, value in (("algorithm", "RSA"), ("keyId", "unknown"), ("value", "AA==")):
            candidate = dict(signature)
            candidate[key] = value
            with self.subTest(key=key):
                with self.assertRaises(validator.ValidationError):
                    validator.validate_signature(candidate)

    def test_published_documents_and_metadata_are_immutable(self):
        current = validator.validate_index(
            self.current_index())
        original_show = validator.git_show
        original_read_bytes = Path.read_bytes

        def baseline(_ref, path):
            return original_read_bytes(validator.ROOT / path)

        validator.git_show = baseline
        try:
            validator.protect_published_content("base", current)

            def tampered(_ref, path):
                content = baseline(_ref, path)
                if path.endswith("/en-US.html"):
                    return content + b"tampered"
                return content

            validator.git_show = tampered
            with self.assertRaises(validator.ValidationError):
                validator.protect_published_content("base", current)
        finally:
            validator.git_show = original_show


if __name__ == "__main__":
    unittest.main()
