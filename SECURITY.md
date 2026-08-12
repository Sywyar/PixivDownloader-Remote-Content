# Security Policy

This repository is a public content origin loaded by PixivDownloader inside a sandboxed iframe. Treat every accepted change as a change to a production trust boundary.

## Report a vulnerability

Please use [GitHub private vulnerability reporting](https://github.com/Sywyar/PixivDownloader-Remote-Content/security/advisories/new). Do not publish exploit details, malicious proof-of-concept HTML, credentials, or user data in a public issue.

Include the affected path or commit, expected impact, and a minimal reproduction. Reports about the consuming application may instead be filed privately in the [PixivDownloader security advisories](https://github.com/Sywyar/PixivDownloader/security/advisories/new).

## Maintainer response

Maintainers should remove an unsafe entry from the mutable index first, then publish a corrected immutable document under a new message ID. Already published files must not be silently replaced because clients and caches may retain either version.
