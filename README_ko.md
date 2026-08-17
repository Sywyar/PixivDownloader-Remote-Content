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
- `master` 브랜치 보호를 활성화하고 `Content validation / validate` 검사를 필수로 지정해야 합니다.
- 공식 Ed25519 신뢰 루트는 색인의 원본 바이트에 서명합니다. 클라이언트는 파싱 전에 서명을 검증하고 만료되거나 순서가 되돌아간 색인을 거부합니다. 각 본문도 색인에 기록된 SHA-256과 일치해야 합니다.
- 색인의 유효 기간은 최대 31일입니다. 색인을 갱신하거나 수정할 때는 `sequence`를 증가시키고 유효 기간과 본문 요약을 갱신해야 하며, 모든 내용이 확정된 뒤 보호된 서명 키로 detached 서명을 새로 생성해야 합니다.
- 게시된 공지 본문과 기존 언어 메타데이터는 수정하거나 삭제할 수 없습니다. 수정본은 새로운 `message-id`로 게시해야 합니다. 기존 공지에 새 언어를 추가할 수 있습니다.
- HTML에는 저장소 검증기가 허용하는 정적 태그, 인라인 CSS 및 제한된 HTTPS 링크만 사용할 수 있습니다. 스크립트, 이벤트 속성, 폼, iframe, 이미지, 글꼴 및 기타 외부 리소스는 금지됩니다.
- 자격 증명, 개인 정보, 사용자 데이터 또는 접근 제어가 필요한 내용을 커밋하지 마세요. 이 저장소와 GitHub Pages의 모든 내용은 공개 정보로 취급합니다.

공지 추가 또는 번역 전에 [CONTRIBUTING.md](CONTRIBUTING.md)를 읽고, 보안 문제는 [SECURITY.md](SECURITY.md)의 안내에 따라 비공개로 보고하세요. 로컬 검증:

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

이 저장소는 [MIT License](LICENSE)를 따릅니다. PixivDownloader 애플리케이션에는 주 저장소에 명시된 별도의 라이선스가 적용됩니다.
