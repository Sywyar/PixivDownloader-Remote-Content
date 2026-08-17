# PixivDownloader Remote Content

[简体中文](README.md)

This repository stores remote static content published to administrators of [Sywyar/PixivDownloader](https://github.com/Sywyar/PixivDownloader). It currently contains announcement documents and their index. GitHub Pages publishes the files directly; there is no server-side application or dynamic build step.

## Announcement URLs

- Index: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json`
- Index signature: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig`
- Document: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html`
- Source: `announcements/<message-id>/<locale>.html` on the `master` branch

Locales use canonical BCP 47 tags such as `zh-CN`, `en-US`, and `zh-Hant`. The client selects a locale from the index and applies its own locale fallback rules when no exact document exists.

## Publishing and security boundary

- Configure GitHub Pages to publish from the repository root on `master` and enforce HTTPS.
- Protect `master` and require the `Content validation / validate` check.
- The official Ed25519 trust root signs the exact index bytes. The client verifies the signature before parsing and rejects expired or rolled-back indexes; every document must also match its SHA-256 in the index.
- An index is valid for at most 31 days. Renewal or any index change must increase `sequence`, refresh the validity window and document digests, and receive a new detached signature from a maintainer after all bytes are final. Ship a new trust root in the client before rotating the signing key.
- Published announcement documents and existing locale metadata are immutable. Publish corrections under a new `message-id`. New locales may be added to an existing announcement.
- HTML may contain only the static elements, inline CSS, and controlled HTTPS links accepted by the repository validator. Scripts, event attributes, forms, iframes, images, fonts, and other external resources are prohibited.
- Never commit credentials, personal information, user data, or anything requiring access control. Treat every file in this repository and on GitHub Pages as public.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before adding or translating an announcement. Report security issues privately as described in [SECURITY.md](SECURITY.md). Run the local validator with:

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

This repository is licensed under the [MIT License](LICENSE). The PixivDownloader application is governed by the separate license declared in its main repository.
