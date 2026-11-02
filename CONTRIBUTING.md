# 贡献指南 / Contributing

本指南说明如何新增公告、补充多语言翻译并执行本地校验。需要 Git、Python 3 与保持 UTF-8 编码的编辑器；最终索引签名由持有受保护签名密钥的维护者生成（见 [README.md](README.md)）。

## 1. 新增公告或补充翻译

1. **确定 `message-id`**：为新公告选择匹配 `[a-z0-9][a-z0-9-]{0,79}` 的唯一小写标识（严禁复用已有 ID 发布不同内容）。
2. **编写多语言 HTML**：在 `announcements/<message-id>/` 下为 `announcements/index.json` 中 `requiredLocales` 列出的全部语言（当前为 `zh-CN`、`en-US`、`zh-Hant`、`ja-JP`、`ko-KR`）创建 `<locale>.html`，直接以现有公告 HTML 为模板。
3. **更新 `announcements/index.json`**：写入该公告的各语言标题、摘要、精确 GitHub Pages URL 及对应 HTML 原始字节的 64 位小写 SHA-256；递增顶层 `sequence`，更新 `generatedAt` 与 `expiresAt`（有效期不超过 31 天）。
4. **本地校验与签名发布**：运行下方验证命令确认全部通过；由维护者使用受保护密钥对定稿后的 `announcements/index.json` 原始字节生成 `announcements/index.json.sig`，在 `Content validation / validate` 通过后发布。

> **注意：** 已发布的 HTML 正文与既有语言元数据不可修改或删除；勘误必须新建 `message-id`。仅为已有公告补充缺失语言时，保持已发布语言文件字节不变，递增 `sequence` 并重新签署索引。

## 2. 受控 HTML 规范

校验器 `scripts/validate_content.py` 强制限制 HTML 结构：

- 仅允许基础语义文本容器、列表、`code`、`strong`、`time` 与 `a` 标签；
- 仅允许单个内联 `<style>`（使用系统字体，禁止 `url()` 与 `@import`）；
- 必须包含与模板完全一致的严格 CSP `<meta>` 标签与 `no-referrer` 策略；
- 外部链接仅允许指向 `https://github.com/Sywyar/PixivDownloader`、PixivDownloader 在线文档，或 `scripts/validate_content.py` 中 `ALLOWED_REFERENCE_LINKS` 显式白名单内的精确 HTTPS 地址；
- 严禁包含脚本、内联事件、表单、iframe、音视频、图片、外部字体或任何外部网络请求。

## 3. 本地校验与线上核验

在仓库根目录依次执行：

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
python scripts/validate_content.py --base-ref origin/master
```

三条命令依次运行校验器单元测试、检查当前索引与全部 HTML、以及对比 `origin/master` 检查已发布内容是否被非法改动，全部退出码必须为 `0`。本地内容校验检查签名文件的格式，不验证 Ed25519 签名；`Content validation / validate` 会另行运行密码学验签。发布上线后，请逐一访问公开的 `index.json` 与新增 `<locale>.html` 页面，确认 GitHub Pages 已提供最新提交内容。

## English summary

1. **Add or translate announcements**: Create `<locale>.html` files under `announcements/<message-id>/` (`[a-z0-9][a-z0-9-]{0,79}`) for every locale in `requiredLocales` (`zh-CN`, `en-US`, `zh-Hant`, `ja-JP`, `ko-KR`). Record the exact GitHub Pages URLs and lowercase SHA-256 digests in `announcements/index.json`, increment `sequence`, and set a validity window of at most 31 days. Published HTML files and existing locale metadata are immutable; use a new `message-id` for corrections.
2. **HTML profile**: Follow an existing HTML file's exact CSP meta tag, `no-referrer` policy, single inline `<style>` (no `url()` / `@import`), and allowlisted HTTPS links (`ALLOWED_REFERENCE_LINKS` in `scripts/validate_content.py`). Scripts, event handlers, forms, iframes, images, and external assets are rejected.
3. **Validation**: Run the three Python commands above before publishing. Local content validation checks the signature file's format; `Content validation / validate` separately verifies the Ed25519 signature. After the maintainer updates `announcements/index.json.sig` and publishes to `master`, verify that GitHub Pages serves the updated URLs.
