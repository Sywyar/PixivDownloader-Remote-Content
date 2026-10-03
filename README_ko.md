# PixivDownloader Remote Content

[简体中文](README.md) · [English](README_en.md)

이 저장소는 [Sywyar/PixivDownloader](https://github.com/Sywyar/PixivDownloader)의 관리자에게 제공되는 원격 정적 콘텐츠를 저장합니다. 현재 공지 본문과 공지 색인을 포함하며, GitHub Pages가 서버 측 프로그램이나 동적 빌드 단계 없이 파일을 직접 게시합니다.

## 공지 주소

- 색인: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json`
- 색인 서명: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig`
- 본문: `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html`
- 소스 파일: `master` 브랜치의 `announcements/<message-id>/<locale>.html`

언어는 `zh-CN`, `en-US`, `zh-Hant`와 같은 표준 BCP 47 태그를 사용합니다. 클라이언트는 색인에서 대상 언어를 선택하고, 일치하는 본문이 없으면 자체 locale 대체 규칙을 적용합니다.

## 게시 및 보안 경계

- GitHub Pages는 `master` 브랜치의 저장소 루트에서 게시하고 HTTPS를 강제해야 합니다.
- `master`의 모든 변경은 `Content validation / validate` 검사를 통과해야 합니다. 자동 갱신은 `master`에 fast-forward 커밋을 푸시합니다. 직접 푸시를 금지하는 브랜치 보호를 사용하는 경우, 보호를 우회하지 말고 갱신 게시 절차를 먼저 변경해야 합니다.
- 공식 Ed25519 신뢰 루트는 색인의 원본 바이트에 서명합니다. 클라이언트는 파싱 전에 서명을 검증하고 만료되거나 순서가 되돌아간 색인을 거부합니다. 각 본문도 색인에 기록된 SHA-256과 일치해야 합니다.
- 색인의 유효 기간은 최대 31일입니다. 갱신하거나 수정할 때는 `sequence`와 유효 기간을 갱신하고, 모든 내용이 확정된 뒤 보호된 키로 detached 서명을 새로 생성해야 합니다. 본문 해시는 파일과 일치해야 하며, 유효 기간만 갱신할 때는 공지와 해시를 유지합니다.
- 게시된 공지 본문과 기존 언어 메타데이터는 수정하거나 삭제할 수 없습니다. 수정본은 새로운 `message-id`로 게시해야 합니다. 기존 공지에 새 언어를 추가할 수 있습니다.
- HTML에는 저장소 검증기가 허용하는 정적 태그, 인라인 CSS 및 제한된 HTTPS 링크만 사용할 수 있습니다. 스크립트, 이벤트 속성, 폼, iframe, 이미지, 글꼴 및 기타 외부 리소스는 금지됩니다.
- 자격 증명, 개인 정보, 사용자 데이터 또는 접근 제어가 필요한 내용을 커밋하지 마세요. 이 저장소와 GitHub Pages의 모든 내용은 공개 정보로 취급합니다.

공지 추가 또는 번역 전에 [CONTRIBUTING.md](CONTRIBUTING.md)를 읽고, 보안 문제는 [SECURITY.md](SECURITY.md)의 안내에 따라 비공개로 보고하세요. 로컬 검증:

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

## 자동 갱신

`Renew announcement index`는 매일 03:37 UTC에 확인하며 Actions에서 `master`를 선택해 수동 실행할 수도 있습니다. 만료까지 7일 이하이거나 이미 만료된 경우 원래 서명과 콘텐츠를 검증한 뒤 `sequence`를 1 증가시키고 `generatedAt`과 30일 후의 `expiresAt`을 설정합니다. 공지 항목, 본문, SHA-256은 변경하지 않습니다. 갱신 시점이 아니면 서명하거나 커밋하지 않습니다.

저장소에 `announcement-signing` Environment를 만들고 배포 브랜치를 `master`로 제한하세요. `PLUGIN_SIGNING_PRIVATE_KEY_PEM_BASE64` Secret에는 현재 공식 Ed25519 PKCS#8 PEM 개인 키를 Base64로 인코딩해 저장합니다. 클라이언트의 `pixivdownloader-official-root-2026-07` 신뢰 루트와 일치해야 하며 임의의 새 키는 검증에 실패합니다. 무인 실행에는 required reviewers를 설정하지 마세요. 검토자를 설정하면 승인을 기다립니다. 키를 Issue, 로그 또는 저장소 파일에 기록하지 마세요.

고정된 소스 커밋의 기존 서명 CLI를 사용합니다. 개인 키는 서명 단계에서 runner 임시 디렉터리에만 저장하고 종료 시 삭제합니다. 검증이 끝나면 색인과 서명을 하나의 커밋으로 게시합니다. `master`가 동시에 변경되면 푸시가 실패하며 다음 실행에서 최신 상태로 다시 시도합니다. 강제 푸시나 자동 병합은 하지 않습니다.

저장소의 `GITHUB_TOKEN`으로 푸시한 뒤 Pages 빌드를 요청하고 해당 커밋의 게시를 기다립니다. 커밋 후 Pages가 실패하면 다음 실행에서 다시 서명하지 않고 현재 `master`의 게시를 복구합니다. 게시 작업은 Contents 읽기와 Pages 쓰기, 서명 작업은 Contents 쓰기 권한만 사용합니다. Actions 실행과 `master` 쓰기를 허용하고 Pages 소스를 `master` 루트로 설정해야 합니다. GitHub가 예약 실행을 비활성화하면 관리자가 다시 활성화하거나 수동 실행해야 합니다. 워크플로를 비활성화하면 자동 갱신과 게시 복구가 중단됩니다.

이 저장소는 [MIT License](LICENSE)를 따릅니다. PixivDownloader 애플리케이션에는 주 저장소에 명시된 별도의 라이선스가 적용됩니다.
