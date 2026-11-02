# PixivDownloader Remote Content

[简体中文](README.md) · [한국어](README_ko.md)

This repository hosts official announcements read by [PixivDownloader](https://github.com/Sywyar/PixivDownloader) administrators inside the application. GitHub Pages publishes the localized static HTML documents, JSON index, and detached Ed25519 signature directly from the root of the `master` branch.

- Add or translate announcements: see [CONTRIBUTING.md](CONTRIBUTING.md)
- Report security issues privately: see [SECURITY.md](SECURITY.md)

## 1. Public URLs and layout

| Resource | URL or Path |
| --- | --- |
| Announcement index | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json` |
| Index signature | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig` |
| Announcement HTML | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html` |
| Source files | `announcements/<message-id>/<locale>.html` on `master` |

Locales use canonical BCP 47 tags (currently requiring `zh-CN`, `en-US`, `zh-Hant`, `ja-JP`, and `ko-KR`). The client caches verified snapshots locally and applies its own locale fallback rules when a locale is absent.

## 2. Security and publishing constraints

- **Pre-parse signature and digest binding**: The raw bytes of `announcements/index.json` are signed with the official Ed25519 trust root (`pixivdownloader-official-root-2026-07`). Clients verify the detached signature before parsing JSON, enforce the validity window and monotonically increasing `sequence`, and verify each HTML file against its indexed SHA-256.
- **Validity window and immutability**: An index is valid for at most 31 days. Every edit or renewal must increment `sequence`, update `generatedAt` and `expiresAt`, and regenerate `index.json.sig`. Release a client that trusts the new key before rotating the signing key. **Published HTML files and existing locale metadata are immutable**; publish corrections under a new `message-id` (adding a new locale to an existing announcement is permitted).
- **Restricted static HTML**: Only static text/layout tags, a single inline `<style>` block, the required restrictive CSP meta tag, `no-referrer`, and allowlisted HTTPS links accepted by `scripts/validate_content.py` are permitted. Scripts, event handlers, forms, iframes, images, external fonts, and network requests are prohibited.
- **Public repository**: Treat all files in this repository and on GitHub Pages as public; never commit credentials, personal data, or non-public information.

Run local unit tests and content validation from the repository root (requires Python 3):

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

## 3. Automatic index renewal (`Renew announcement index`)

The workflow runs daily at `03:37 UTC` on `master` (and supports manual `workflow_dispatch`):

- **Trigger**: When the index has 7 days or less remaining (or has expired), the workflow verifies the existing signature and HTML digests, increments `sequence` by `1`, updates `generatedAt`, and sets `expiresAt` to 30 days later while keeping announcement entries and SHA-256 digests unchanged. Outside that window, it does not sign or commit.
- **Environment and secret**: Configure the `announcement-signing` Environment restricted to `master` with the `PLUGIN_SIGNING_PRIVATE_KEY_PEM_BASE64` Secret (Base64-encoded Ed25519 PKCS#8 PEM private key matching `pixivdownloader-official-root-2026-07`). If required reviewers are configured, renewal waits for approval. The key is written only to runner temporary storage during signing and deleted on exit.
- **Publication and recovery**: The signing job (`contents: write`) pushes `index.json` and `index.json.sig` in one fast-forward commit; the publishing job (`contents: read`, `pages: write`) triggers a GitHub Pages build and waits for deployment (if Pages deployment fails after a commit, the next run republishes `master` without re-signing).

Allow Actions to write to `master`, configure Pages to publish from its root, and enable HTTPS. Every change should pass `Content validation / validate`. If branch protection prohibits direct pushes, adapt the renewal workflow without bypassing protection. Disabling the workflow stops automatic renewal and publication recovery; if GitHub disables scheduled runs, a maintainer must re-enable them.

This repository is licensed under the [MIT License](LICENSE).
