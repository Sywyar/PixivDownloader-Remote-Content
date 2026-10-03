# PixivDownloader Remote Content

[简体中文](README.md) · [한국어](README_ko.md)

This repository stores remote static content published to administrators of [Sywyar/PixivDownloader](https://github.com/Sywyar/PixivDownloader). It currently contains announcement documents and their index. GitHub Pages publishes the files directly; there is no server-side application or dynamic build step.

## Announcement URLs

- Index: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json`
- Index signature: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig`
- Document: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html`
- Source: `announcements/<message-id>/<locale>.html` on the `master` branch

Locales use canonical BCP 47 tags such as `zh-CN`, `en-US`, and `zh-Hant`. The client selects a locale from the index and applies its own locale fallback rules when no exact document exists.

## Publishing and security boundary

- Configure GitHub Pages to publish from the repository root on `master` and enforce HTTPS.
- Every change to `master` should pass `Content validation / validate`. Automatic renewal pushes a fast-forward commit to `master`; if branch protection prohibits direct pushes, adapt the publication workflow before enabling it. Do not bypass protection.
- The official Ed25519 trust root signs the exact index bytes. The client verifies the signature before parsing and rejects expired or rolled-back indexes; every document must also match its SHA-256 in the index.
- An index is valid for at most 31 days. Renewal or any index change must increase `sequence`, refresh the validity window, and receive a new detached signature using the protected signing key after all bytes are final. Document digests must match their files; renewal alone preserves announcements and their digests. Ship a new trust root in the client before rotating the signing key.
- Published announcement documents and existing locale metadata are immutable. Publish corrections under a new `message-id`. New locales may be added to an existing announcement.
- HTML may contain only the static elements, inline CSS, and controlled HTTPS links accepted by the repository validator. Scripts, event attributes, forms, iframes, images, fonts, and other external resources are prohibited.
- Never commit credentials, personal information, user data, or anything requiring access control. Treat every file in this repository and on GitHub Pages as public.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before adding or translating an announcement. Report security issues privately as described in [SECURITY.md](SECURITY.md). Run the local validator with:

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

## Automatic renewal

`Renew announcement index` checks daily at 03:37 UTC and can also run manually from Actions on `master`. When the index has at most 7 days left, including when it has expired, the workflow verifies the original signature and content, increments `sequence`, updates `generatedAt`, and sets `expiresAt` to 30 days after generation. Announcement entries, documents, and SHA-256 values stay unchanged. An index outside the renewal window causes no signing or commit.

Before enabling renewal, create an `announcement-signing` Environment in this repository, allow deployments only from `master`, and add the `PLUGIN_SIGNING_PRIVATE_KEY_PEM_BASE64` Secret. Its value must be the Base64 encoding of the current official Ed25519 PKCS#8 PEM private key, matching the client's built-in `pixivdownloader-official-root-2026-07` trust root. An unrelated new key will fail verification. Omit required reviewers for unattended renewal; configuring reviewers makes renewal wait for approval. Never put the key in issues, logs, or repository files.

The workflow uses the existing signature CLI from a pinned source commit. The signing step writes the key only to runner temporary storage and deletes it on exit. After signature and content checks pass, it publishes the index and signature in one commit. Concurrent changes to `master` reject the push; a later run starts from the new mainline without forcing or merging changes.

After pushing with this repository's `GITHUB_TOKEN`, the workflow explicitly requests a Pages build and waits for publication of the expected commit. If the commit succeeds but Pages fails, the next run checks and republishes the current `master` without another renewal. Publication uses only Contents read and Pages write; signing uses only Contents write. Actions must be enabled and permitted to write `master`, with Pages publishing from its root. If GitHub disables the schedule, a maintainer must re-enable it or run it manually. Disable the workflow to stop automatic renewal and publication recovery.

This repository is licensed under the [MIT License](LICENSE). The PixivDownloader application is governed by the separate license declared in its main repository.
