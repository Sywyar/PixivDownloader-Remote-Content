#!/usr/bin/env python3
"""Validate the public announcement index and its deliberately small HTML profile."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "announcements" / "index.json"
SIGNATURE_PATH = ROOT / "announcements" / "index.json.sig"
PUBLIC_BASE = "https://sywyar.github.io/PixivDownloader-Remote-Content/"
OFFICIAL_KEY_ID = "pixivdownloader-official-root-2026-07"
MAX_INDEX_VALIDITY = timedelta(days=31)
CONTENT_SECURITY_POLICY = (
    "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; "
    "img-src 'none'; font-src 'none'; connect-src 'none'; media-src 'none'; "
    "object-src 'none'; frame-src 'none'; child-src 'none'; worker-src 'none'; "
    "form-action 'none'; base-uri 'none'"
)
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,79}\Z")
LOCALE_RE = re.compile(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})+\Z")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
BLOCKED_CSS_RE = re.compile(
    r"url\s*\(|@import|@font-face|(?:image|image-set|cross-fade|element|paint|linear-gradient|"
    r"radial-gradient|conic-gradient|repeating-linear-gradient|repeating-radial-gradient)\s*\(|"
    r"src\s*:|expression\s*\(|behavior\s*:|-moz-binding|/\*|\\",
    re.IGNORECASE,
)
ALLOWED_TAGS = {
    "html", "head", "meta", "title", "style", "body", "main", "article",
    "header", "section", "footer", "h1", "h2", "p", "ul", "li", "strong",
    "a", "time", "code",
}
VOID_TAGS = {"meta"}
ALLOWED_ATTRIBUTES = {
    "html": {"lang"},
    "meta": {"charset", "http-equiv", "name", "content"},
    "a": {"href", "target", "rel"},
    "time": {"datetime"},
}
ALLOWED_PARENTS = {
    "html": {None},
    "head": {"html"},
    "meta": {"head"},
    "title": {"head"},
    "style": {"head"},
    "body": {"html"},
    "main": {"body"},
    "article": {"main"},
    "header": {"article"},
    "section": {"article"},
    "footer": {"article"},
    "h1": {"header"},
    "h2": {"section"},
    "p": {"header", "section", "footer"},
    "ul": {"section"},
    "li": {"ul"},
    "strong": {"p", "li"},
    "a": {"p", "li"},
    "time": {"p"},
    "code": {"p", "li"},
}


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_keys(value: dict, expected: set[str], context: str) -> None:
    require(set(value) == expected, f"{context}: expected keys {sorted(expected)}")


def safe_text(value: object, context: str, maximum: int) -> str:
    require(isinstance(value, str), f"{context}: expected a string")
    require(value == value.strip() and 0 < len(value) <= maximum,
            f"{context}: must contain 1..{maximum} trimmed characters")
    require(not CONTROL_RE.search(value), f"{context}: control character is forbidden")
    return value


def utc_timestamp(value: object, context: str) -> datetime:
    timestamp = safe_text(value, context, 32)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{context}: invalid RFC 3339 timestamp") from error
    require(timestamp.endswith("Z") and parsed.utcoffset() is not None,
            f"{context}: UTC Z timestamp required")
    return parsed


def validate_link(value: str, context: str) -> None:
    require(len(value.encode("utf-8")) <= 2048 and not CONTROL_RE.search(value)
            and "\\" not in value and "%" not in value,
            f"{context}: link is not canonical")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ValidationError(f"{context}: malformed link") from error
    require(parsed.scheme == "https" and parsed.username is None
            and parsed.password is None and port is None
            and parsed.netloc in {"github.com", "sywyar.github.io"}
            and parsed.geturl() == value,
            f"{context}: only canonical HTTPS links are allowed")
    require(not parsed.query, f"{context}: query strings are forbidden")
    if parsed.hostname == "github.com":
        require(parsed.path == "/Sywyar/PixivDownloader"
                or parsed.path.startswith("/Sywyar/PixivDownloader/"),
                f"{context}: GitHub link must stay under Sywyar/PixivDownloader")
    elif parsed.hostname == "sywyar.github.io":
        require(parsed.path == "/PixivDownloader/"
                or parsed.path.startswith("/PixivDownloader/"),
                f"{context}: documentation link must stay under PixivDownloader")
    else:
        raise ValidationError(f"{context}: host is not allowlisted")


class AnnouncementParser(HTMLParser):
    def __init__(self, path: Path, locale: str, title: str) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.locale = locale
        self.expected_title = title
        self.stack: list[str] = []
        self.counts: dict[str, int] = {}
        self.declarations: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.style_parts: list[str] = []
        self.title_parts: list[str] = []

    def fail(self, message: str) -> None:
        raise ValidationError(f"{self.path.relative_to(ROOT)}: {message}")

    def handle_decl(self, decl: str) -> None:
        self.declarations.append(decl)

    def handle_comment(self, data: str) -> None:
        self.fail("HTML comments are forbidden")

    def handle_pi(self, data: str) -> None:
        self.fail("processing instructions are forbidden")

    def handle_entityref(self, name: str) -> None:
        self.fail("unresolved entity reference")

    def handle_charref(self, name: str) -> None:
        self.fail("unresolved character reference")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        require(tag in ALLOWED_TAGS, f"{self.path.relative_to(ROOT)}: <{tag}> is forbidden")
        parent = self.stack[-1] if self.stack else None
        require(parent in ALLOWED_PARENTS[tag],
                f"{self.path.relative_to(ROOT)}: <{tag}> is not allowed below <{parent}>")
        names = [name for name, _ in attrs]
        require(len(names) == len(set(names)),
                f"{self.path.relative_to(ROOT)}: duplicate attribute on <{tag}>")
        allowed = ALLOWED_ATTRIBUTES.get(tag, set())
        require(set(names) <= allowed,
                f"{self.path.relative_to(ROOT)}: forbidden attribute on <{tag}>")
        values = {name: value or "" for name, value in attrs}
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if tag == "html":
            require(values == {"lang": self.locale},
                    f"{self.path.relative_to(ROOT)}: html lang must match the locale filename")
        elif tag == "meta":
            self.meta.append(values)
        elif tag == "a":
            require(set(values) == {"href", "target", "rel"},
                    f"{self.path.relative_to(ROOT)}: links need href, target, and rel")
            require(values["target"] == "_blank"
                    and set(values["rel"].split()) == {"noopener", "noreferrer"},
                    f"{self.path.relative_to(ROOT)}: links need an isolated external target")
            validate_link(values["href"], str(self.path.relative_to(ROOT)))
        elif tag == "time":
            require(set(values) == {"datetime"} and DATE_RE.fullmatch(values["datetime"]),
                    f"{self.path.relative_to(ROOT)}: time needs an ISO date")
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        require(tag not in VOID_TAGS and self.stack and self.stack[-1] == tag,
                f"{self.path.relative_to(ROOT)}: mismatched </{tag}>")
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        require(not CONTROL_RE.search(data),
                f"{self.path.relative_to(ROOT)}: control character is forbidden")
        if self.stack and self.stack[-1] == "style":
            self.style_parts.append(data)
        elif self.stack and self.stack[-1] == "title":
            self.title_parts.append(data)
        elif not self.stack and data.strip():
            self.fail("text outside the document is forbidden")

    def close_and_validate(self) -> None:
        self.close()
        require(not self.stack, f"{self.path.relative_to(ROOT)}: unclosed tag")
        require(self.declarations == ["doctype html"],
                f"{self.path.relative_to(ROOT)}: exactly one HTML5 doctype is required")
        for tag in ("html", "head", "title", "style", "body", "main", "article", "header", "footer"):
            require(self.counts.get(tag) == 1,
                    f"{self.path.relative_to(ROOT)}: exactly one <{tag}> is required")
        required_meta = [
            {"charset": "utf-8"},
            {"http-equiv": "Content-Security-Policy", "content": CONTENT_SECURITY_POLICY},
            {"name": "referrer", "content": "no-referrer"},
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        ]
        require(self.meta == required_meta,
                f"{self.path.relative_to(ROOT)}: security and viewport meta tags must be exact")
        require("".join(self.title_parts).strip() == self.expected_title,
                f"{self.path.relative_to(ROOT)}: <title> must match index.json")
        css = "".join(self.style_parts)
        require(css.strip() and not BLOCKED_CSS_RE.search(css),
                f"{self.path.relative_to(ROOT)}: CSS contains an external-resource mechanism")


def load_index_bytes(data: bytes, context: str) -> dict:
    def unique_object(pairs: list[tuple[str, object]]) -> dict:
        value: dict[str, object] = {}
        for key, item in pairs:
            require(key not in value, f"{context}: duplicate JSON key {key!r}")
            value[key] = item
        return value

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"{context}: invalid UTF-8 JSON: {error}") from error
    require(isinstance(value, dict), f"{context}: root must be an object")
    return value


def validate_index(value: dict) -> dict[str, dict]:
    require_keys(value, {"schemaVersion", "sequence", "generatedAt", "expiresAt",
                         "requiredLocales", "announcements"}, "index.json")
    require(value["schemaVersion"] == 1, "index.json: unsupported schemaVersion")
    require(isinstance(value["sequence"], int) and not isinstance(value["sequence"], bool)
            and value["sequence"] > 0, "index.json: sequence must be a positive integer")
    generated_at = utc_timestamp(value["generatedAt"], "index.json.generatedAt")
    expires_at = utc_timestamp(value["expiresAt"], "index.json.expiresAt")
    require(generated_at < expires_at <= generated_at + MAX_INDEX_VALIDITY,
            "index.json: validity must be positive and no longer than 31 days")
    locales = value["requiredLocales"]
    require(isinstance(locales, list) and locales and len(locales) == len(set(locales)),
            "index.json: requiredLocales must be a non-empty unique array")
    for locale in locales:
        require(isinstance(locale, str) and LOCALE_RE.fullmatch(locale),
                f"index.json: invalid locale {locale!r}")
    announcements = value["announcements"]
    require(isinstance(announcements, list), "index.json: announcements must be an array")
    by_id: dict[str, dict] = {}
    expected_files: set[Path] = set()
    for position, item in enumerate(announcements):
        context = f"index.json announcements[{position}]"
        require(isinstance(item, dict), f"{context}: expected an object")
        require_keys(item, {"id", "publishedAt", "severity", "locales"}, context)
        message_id = safe_text(item["id"], f"{context}.id", 80)
        require(ID_RE.fullmatch(message_id), f"{context}.id: invalid message ID")
        require(message_id not in by_id, f"{context}.id: duplicate message ID")
        utc_timestamp(item["publishedAt"], f"{context}.publishedAt")
        require(item["severity"] in {"info", "warning", "critical"},
                f"{context}.severity: unsupported value")
        translations = item["locales"]
        require(isinstance(translations, dict) and set(translations) == set(locales),
                f"{context}.locales: every required locale must be present")
        for locale, translation in translations.items():
            locale_context = f"{context}.locales.{locale}"
            require(isinstance(translation, dict), f"{locale_context}: expected an object")
            require_keys(translation, {"title", "summary", "contentUrl", "contentSha256"},
                         locale_context)
            title = safe_text(translation["title"], f"{locale_context}.title", 160)
            safe_text(translation["summary"], f"{locale_context}.summary", 500)
            digest = translation["contentSha256"]
            require(isinstance(digest, str) and SHA256_RE.fullmatch(digest),
                    f"{locale_context}.contentSha256: lowercase SHA-256 required")
            relative = Path("announcements") / message_id / f"{locale}.html"
            expected_url = PUBLIC_BASE + relative.as_posix()
            require(translation["contentUrl"] == expected_url,
                    f"{locale_context}.contentUrl: must equal {expected_url}")
            path = ROOT / relative
            require(path.is_file() and not path.is_symlink(),
                    f"{relative}: document is missing or is a symlink")
            require(path.stat().st_size <= 256 * 1024,
                    f"{relative}: document exceeds 256 KiB")
            document_bytes = path.read_bytes()
            require(hashlib.sha256(document_bytes).hexdigest() == digest,
                    f"{relative}: SHA-256 does not match index.json")
            try:
                source = document_bytes.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValidationError(f"{relative}: document is not UTF-8") from error
            parser = AnnouncementParser(path, locale, title)
            parser.feed(source)
            parser.close_and_validate()
            expected_files.add(relative)
        by_id[message_id] = item
    repository_files = listed_repository_files()
    for relative in repository_files:
        require(not (ROOT / relative).is_symlink(), f"{relative}: symlinks are forbidden")
    actual_files = {
        relative for relative in repository_files
        if relative.suffix.lower() == ".html"
    }
    require(actual_files == expected_files,
            "announcements: every HTML file must be referenced exactly once by index.json")
    return by_id


def validate_signature(value: dict) -> None:
    require_keys(value, {"formatVersion", "algorithm", "keyId", "value"},
                 "announcements/index.json.sig")
    require(value["formatVersion"] == 1,
            "announcements/index.json.sig: unsupported formatVersion")
    require(value["algorithm"] == "Ed25519",
            "announcements/index.json.sig: unsupported algorithm")
    require(value["keyId"] == OFFICIAL_KEY_ID,
            "announcements/index.json.sig: unexpected keyId")
    signature = value["value"]
    require(isinstance(signature, str) and len(signature) <= 128,
            "announcements/index.json.sig: invalid signature value")
    try:
        decoded = base64.b64decode(signature, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValidationError("announcements/index.json.sig: invalid Base64") from error
    require(len(decoded) == 64,
            "announcements/index.json.sig: Ed25519 signature must be 64 bytes")


def git_show(base_ref: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{base_ref}:{path}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def listed_repository_files() -> set[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(result.returncode == 0, "cannot enumerate repository files")
    try:
        names = result.stdout.decode("utf-8").split("\0")
    except UnicodeDecodeError as error:
        raise ValidationError("repository paths must be UTF-8") from error
    return {Path(name) for name in names if name}


def protect_published_content(base_ref: str, current: dict[str, dict]) -> None:
    old_index_bytes = git_show(base_ref, "announcements/index.json")
    require(old_index_bytes is not None,
            f"base ref {base_ref!r} does not contain announcements/index.json")
    old_index = load_index_bytes(old_index_bytes, f"{base_ref}:announcements/index.json")
    old_sequence = old_index.get("sequence")
    if isinstance(old_sequence, int) and not isinstance(old_sequence, bool):
        require(INDEX_PATH.read_bytes() == old_index_bytes
                or current_index_sequence() > old_sequence,
                "index.json: changed content must increase sequence")
    old_entries = {item["id"]: item for item in old_index.get("announcements", [])}
    for message_id, old_entry in old_entries.items():
        require(message_id in current, f"published announcement {message_id} cannot be removed")
        new_entry = current[message_id]
        for key in ("publishedAt", "severity"):
            require(new_entry.get(key) == old_entry.get(key),
                    f"published announcement {message_id}.{key} is immutable")
        for locale, old_translation in old_entry.get("locales", {}).items():
            new_translation = new_entry.get("locales", {}).get(locale)
            if "contentSha256" not in old_translation:
                require(isinstance(new_translation, dict)
                        and {key: value for key, value in new_translation.items()
                             if key != "contentSha256"} == old_translation,
                        f"published announcement {message_id}/{locale} metadata is immutable")
            else:
                require(new_translation == old_translation,
                        f"published announcement {message_id}/{locale} metadata is immutable")
            relative = f"announcements/{message_id}/{locale}.html"
            old_document = git_show(base_ref, relative)
            require(old_document is not None and (ROOT / relative).read_bytes() == old_document,
                    f"published document {relative} is immutable")


def current_index_sequence() -> int:
    return load_index_bytes(INDEX_PATH.read_bytes(), "announcements/index.json")["sequence"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", help="Git commit used to enforce published immutability")
    args = parser.parse_args()
    try:
        require(INDEX_PATH.is_file() and not INDEX_PATH.is_symlink(),
                "announcements/index.json is missing or is a symlink")
        require(INDEX_PATH.stat().st_size <= 1024 * 1024,
                "announcements/index.json exceeds 1 MiB")
        require(SIGNATURE_PATH.is_file() and not SIGNATURE_PATH.is_symlink(),
                "announcements/index.json.sig is missing or is a symlink")
        require(SIGNATURE_PATH.stat().st_size <= 16 * 1024,
                "announcements/index.json.sig exceeds 16 KiB")
        index = load_index_bytes(INDEX_PATH.read_bytes(), "announcements/index.json")
        signature = load_index_bytes(SIGNATURE_PATH.read_bytes(),
                                     "announcements/index.json.sig")
        validate_signature(signature)
        current = validate_index(index)
        if args.base_ref:
            protect_published_content(args.base_ref, current)
    except (OSError, ValidationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(current)} announcement(s) and "
          f"{sum(len(item['locales']) for item in current.values())} document(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
