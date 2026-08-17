# Contributing

## Add an announcement

1. Choose a stable lowercase `message-id` matching `[a-z0-9][a-z0-9-]{0,79}`. Never reuse an ID for different content.
2. Create one HTML document for every locale in `announcements/index.json`'s `requiredLocales` list, currently `zh-CN.html`, `en-US.html`, and `zh-Hant.html`. Use an existing document as the template.
3. Add one entry to `announcements/index.json`. Every locale entry must point to its exact GitHub Pages URL and contain the lowercase SHA-256 of the exact HTML bytes.
4. Increase `sequence` and refresh `generatedAt` and `expiresAt`; the validity window must not exceed 31 days.
5. Run `python -m unittest discover -s scripts -p "test_*.py"` and `python scripts/validate_content.py`, then review every listed locale.
6. Submit the change through a pull request. After all bytes are final, a maintainer updates `announcements/index.json.sig` with the protected signing key and waits for the required validation check.

Published HTML and existing locale metadata are immutable. A correction is a new announcement with a new ID. Adding a previously missing locale is allowed, but changing or removing a published locale is not.
Every index change, including a validity renewal or added translation, needs a larger sequence and a new detached signature. Signing-key rotation requires a client release that trusts the new key before the remote index starts using it.

## HTML profile

The validator intentionally accepts a small document language:

- semantic text containers, lists, `code`, `strong`, `time`, and links;
- one inline `<style>` block using system fonts and no `url()` or `@import`;
- an exact restrictive CSP meta tag and `no-referrer` policy;
- HTTPS links only to `github.com/Sywyar/PixivDownloader` or the PixivDownloader GitHub Pages documentation.

Do not add scripts, event handlers, forms, frames, media, embedded data, external styles, fonts, images, tracking, redirects, or network requests. Do not add a dependency or site generator unless the static format can no longer satisfy an actual requirement.

## Translate existing announcements

Add `<locale>.html` beside each announcement currently listed in the index, then add that locale's title, summary, and immutable content URL to the matching index entry. Do not alter existing locale files. Translation work must also follow the main PixivDownloader repository's i18n workflow.
