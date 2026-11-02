# PixivDownloader Remote Content

[简体中文](README.md) · [English](README_en.md)

이 저장소는 [PixivDownloader](https://github.com/Sywyar/PixivDownloader) 관리자가 앱 내에서 읽는 공식 공지를 호스팅합니다. GitHub Pages는 `master` 브랜치 루트에서 다국어 정적 HTML 본문, JSON 색인 및 Ed25519 분리 서명을 직접 게시합니다.

- 공지 추가 및 번역: [CONTRIBUTING.md](CONTRIBUTING.md)
- 보안 취약점 비공개 보고: [SECURITY.md](SECURITY.md)

## 1. 공개 주소 및 구조

| 리소스 | 주소 또는 경로 |
| --- | --- |
| 공지 색인 | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json` |
| 색인 서명 | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig` |
| 공지 본문 | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html` |
| 소스 경로 | `master` 브랜치의 `announcements/<message-id>/<locale>.html` |

언어는 표준 BCP 47 태그(현재 필수 언어: `zh-CN`, `en-US`, `zh-Hant`, `ja-JP`, `ko-KR`)를 사용합니다. 클라이언트는 검증된 스냅샷을 로컬에 저장하며, 해당 언어가 없으면 앱 자체의 locale 대체 규칙을 적용합니다.

## 2. 보안 및 게시 제약

- **사전 서명 검증 및 해시 바인딩**: `announcements/index.json` 원본 바이트는 공식 신뢰 루트(`pixivdownloader-official-root-2026-07`)로 Ed25519 서명됩니다. 클라이언트는 JSON 파싱 전에 서명, 유효 기간, 단조 증가하는 `sequence`를 검증하고 각 HTML 본문의 SHA-256을 대조합니다.
- **유효 기간 및 불변성**: 색인의 유효 기간은 최대 31일입니다. 수정이나 갱신 시마다 `sequence`를 증가시키고 `generatedAt` / `expiresAt` 및 `index.json.sig`를 새로 생성해야 합니다. 서명 키를 교체하기 전에 새 키를 신뢰하는 클라이언트를 먼저 배포해야 합니다. **이미 게시된 공지 HTML과 기존 언어 메타데이터는 수정하거나 삭제할 수 없으며**, 정정이 필요한 경우 새 `message-id`로 게시해야 합니다(기존 공지에 새 언어를 추가하는 것은 허용됨).
- **제한된 정적 HTML**: `scripts/validate_content.py`가 허용하는 정적 텍스트 태그, 단일 인라인 `<style>`, 엄격한 CSP meta, `no-referrer` 및 허용된 HTTPS 링크만 사용할 수 있습니다. 스크립트, 이벤트 속성, 폼, iframe, 이미지, 외부 글꼴 및 외부 네트워크 요청은 금지됩니다.
- **공개 범위**: 이 저장소와 GitHub Pages의 모든 파일은 공개 정보이므로 자격 증명, 개인 정보 또는 비공개 데이터를 커밋하지 마세요.

저장소 루트에서 로컬 테스트 및 콘텐츠 검증을 실행합니다(Python 3 필요):

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

## 3. 색인 자동 갱신 (`Renew announcement index`)

워크플로는 매일 `03:37 UTC`에 `master`를 확인합니다(Actions에서 수동 실행 가능):

- **실행 조건**: 만료까지 7일 이하(만료 포함)일 때 기존 서명과 본문 해시를 검증한 뒤 `sequence`를 `1` 증가시키고 `generatedAt`과 30일 후의 `expiresAt`을 설정합니다(공지 항목과 본문 SHA-256은 유지). 이 조건에 해당하지 않으면 서명하거나 커밋하지 않습니다.
- **Environment 및 키 설정**: `master`만 배포할 수 있는 `announcement-signing` Environment를 생성하고 `PLUGIN_SIGNING_PRIVATE_KEY_PEM_BASE64` Secret(내장 신뢰 루트에 대응하는 Ed25519 PKCS#8 PEM 개인 키 Base64)을 설정합니다. required reviewers를 설정하면 갱신 작업이 승인을 기다립니다. 개인 키는 서명 단계의 임시 디렉터리에만 기록되고 종료 시 삭제됩니다.
- **게시 및 복구**: 서명 작업(`contents: write`)이 단일 fast-forward 커밋으로 `index.json`과 `index.json.sig`를 푸시하면 게시 작업(`contents: read`, `pages: write`)이 Pages 빌드를 요청하고 배포 완료를 확인합니다(커밋 후 Pages 배포만 실패한 경우 다음 실행에서 재서명 없이 현재 `master`를 다시 배포합니다).

Actions가 `master`에 쓸 수 있도록 허용하고, Pages 게시 소스를 `master` 루트로 설정한 뒤 HTTPS를 활성화해야 합니다. 모든 변경은 `Content validation / validate`를 통과해야 합니다. 브랜치 보호가 직접 푸시를 금지하면 보호를 우회하지 말고 갱신 흐름을 조정하세요. 워크플로를 비활성화하면 자동 갱신과 재게시가 중지됩니다. GitHub가 예약 실행을 중지한 경우 유지관리자가 다시 활성화해야 합니다.

이 저장소는 [MIT License](LICENSE)를 따릅니다.
