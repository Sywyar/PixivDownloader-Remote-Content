# PixivDownloader Remote Content

[English](README_en.md) · [한국어](README_ko.md)

本仓库托管 [PixivDownloader](https://github.com/Sywyar/PixivDownloader) 管理员在应用内读取的官方公告。GitHub Pages 从 `master` 分支根目录发布多语言静态 HTML 正文、JSON 索引与 Ed25519 独立签名。

- 新增或翻译公告：见 [CONTRIBUTING.md](CONTRIBUTING.md)
- 私密报告安全问题：见 [SECURITY.md](SECURITY.md)

## 1. 公开地址与目录结构

| 资源 | 地址或路径 |
| --- | --- |
| 公告索引 | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json` |
| 索引签名 | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig` |
| 公告正文 | `https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html` |
| 源码路径 | `master` 分支 `announcements/<message-id>/<locale>.html` |

语言标识使用规范化 BCP 47 标签（当前必选语言为 `zh-CN`、`en-US`、`zh-Hant`、`ja-JP`、`ko-KR`）；客户端按索引拉取并保存在本地，缺失时按应用自身的 locale 回退规则显示。

## 2. 安全与发布约束

- **先验签名与摘要绑定**：`announcements/index.json` 原始字节由官方信任根（`pixivdownloader-official-root-2026-07`）签署 Ed25519 detached 签名。客户端在解析 JSON 前先验签，校验有效期与单调递增的 `sequence`，并核对每份 HTML 正文的精确 SHA-256。
- **有效期与不可变性**：索引有效期最长 31 天；每次修改或续期均须递增 `sequence`、刷新 `generatedAt` / `expiresAt` 并重新生成 `index.json.sig`。轮换签名密钥前，须先发布信任新密钥的客户端。**已发布的公告 HTML 与既有语言元数据不可修改或删除**；订正内容必须使用新的 `message-id`（允许为已有公告补齐新语言）。
- **受控静态 HTML**：仅允许 `scripts/validate_content.py` 白名单内的静态排版标签、单个内联 `<style>`、严格 CSP meta、`no-referrer` 以及受控 HTTPS 链接；禁止脚本、事件属性、表单、iframe、图片、外部字体或任何外部网络请求。
- **公开边界**：本仓库及 GitHub Pages 上的全部文件均为公开信息，严禁提交凭据、个人信息或非公开数据。

在仓库根目录运行本地测试与内容校验（需 Python 3）：

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

## 3. 索引自动续签（`Renew announcement index`）

工作流每日 `03:37 UTC` 检查 `master`（也可在 Actions 中手动触发）：

- **触发条件**：当索引距到期不超过 7 天（含已过期）时，先验证原签名与正文摘要，随后将 `sequence` 加 `1`、更新 `generatedAt` 并将 `expiresAt` 延长至生成时间后 30 天（公告条目与正文 SHA-256 保持不变）；未临期时不执行签名或提交。
- **Environment 与密钥配置**：在仓库创建仅允许 `master` 部署的 `announcement-signing` Environment，并配置 `PLUGIN_SIGNING_PRIVATE_KEY_PEM_BASE64` Secret（对应内置官方信任根的 Ed25519 PKCS#8 PEM 私钥 Base64）。配置 required reviewers 后，续签会等待审批。私钥仅在签名步骤写入 runner 临时目录并在退出时删除。
- **发布与补发**：签名作业（`contents: write`）以单个快进提交推送 `index.json` 与 `index.json.sig`；发布作业（`contents: read`、`pages: write`）随后请求 GitHub Pages 构建并轮询至线上生效（若提交成功但 Pages 构建失败，下次运行会自动补发当前 `master` 而无需重复续签）。

仓库须允许 Actions 向 `master` 写入，并将 Pages 来源设为 `master` 根目录、启用 HTTPS。每次修改应通过 `Content validation / validate`；如果分支保护禁止直推，须先调整续签流程，不能绕过保护。禁用该工作流可停止自动续签和补发；GitHub 停用定时任务后需由维护者重新启用。

本仓库采用 [MIT License](LICENSE)。
