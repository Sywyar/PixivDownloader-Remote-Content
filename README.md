# PixivDownloader Remote Content

[English](README_en.md) · [한국어](README_ko.md)

本仓库保存 [Sywyar/PixivDownloader](https://github.com/Sywyar/PixivDownloader) 面向管理员发布的远程静态内容，目前包括公告正文与公告索引。内容由 GitHub Pages 直接发布，不包含服务端程序或动态构建步骤。

## 公告地址

- 索引：`https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json`
- 索引签名：`https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig`
- 正文：`https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html`
- 源文件：`master` 分支的 `announcements/<message-id>/<locale>.html`

语言使用规范化 BCP 47 tag，例如 `zh-CN`、`en-US`、`zh-Hant`。客户端从索引选择目标语言；缺失时按应用自己的 locale 回退规则处理。

## 发布与安全边界

- GitHub Pages 应配置为从 `master` 分支仓库根目录发布，并强制 HTTPS。
- `master` 的每次修改都应通过 `Content validation / validate`。自动续签会向 `master` 快进提交；如启用禁止直推的分支保护，须先调整续签发布流程，不能绕过保护。
- 公告索引原始字节使用官方 Ed25519 信任根签名。客户端在解析前验签，并拒绝过期或序列回退的索引；每份正文还必须匹配索引中的 SHA-256。
- 索引最长有效 31 天。续期或修改索引时必须递增 `sequence`、更新有效期，并在全部内容定稿后使用受保护的签名密钥重新生成 detached 签名。正文摘要必须与对应文件一致；单纯续期保留公告及其摘要。轮换签名密钥时，应先在客户端发布新的信任根。
- 已发布的公告正文和既有语言元数据不可修改或删除；修订内容时创建新的 `message-id`。可以为已有公告追加新的语言。
- HTML 只能使用仓库校验器允许的静态标签、内联 CSS 和受控 HTTPS 链接；禁止脚本、事件属性、表单、iframe、图片、字体及其它外部资源。
- 不得提交凭据、个人信息、用户数据或任何需要访问控制的内容。本仓库及 GitHub Pages 上的全部内容均视为公开信息。

新增或翻译公告前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题请按 [SECURITY.md](SECURITY.md) 私下报告。运行本地校验：

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

## 自动续签

`Renew announcement index` 每天 03:37 UTC 检查索引，也可在 Actions 中选择 `master` 手动运行。距离到期不超过 7 天（包括已过期）时，它先验证原签名和公告内容，再将 `sequence` 加一、更新 `generatedAt`，并把 `expiresAt` 设为生成时间后的 30 天。公告条目、正文和 SHA-256 保持不变。未临期时不签名、不提交。

启用前，在本仓库创建 `announcement-signing` Environment，只允许 `master` 部署，并配置 `PLUGIN_SIGNING_PRIVATE_KEY_PEM_BASE64` Secret，值为当前官方 Ed25519 PKCS#8 PEM 私钥的 Base64。它必须对应客户端内置的 `pixivdownloader-official-root-2026-07` 信任根；任意新密钥都会被验签拒绝。需要全自动运行时不要设置人工审批；如设置 required reviewers，续签会等待批准。不要把密钥粘贴到 Issue、日志或仓库文件中。

工作流使用固定源码 SHA 的现有签名 CLI。私钥只在签名步骤写入 runner 临时目录，退出时删除；验签和内容校验成功后，索引与签名在同一个提交中发布。主线发生并发变化时推送失败，后续运行从新主线重试，不强推或自动合并。

机器人使用本仓库的 `GITHUB_TOKEN` 推送后，会显式请求 Pages 构建并等待对应提交发布。如果提交成功而 Pages 失败，下一次运行会检查并补发当前 `master`，无需再次续签。该步骤只使用 Contents 读和 Pages 写权限；签名作业只使用 Contents 写权限。仓库仍须允许 Actions 运行、向 `master` 写入，并将 Pages 来源设为 `master` 根目录。GitHub 停用定时任务时，维护者须重新启用工作流或手动运行；禁用该工作流可停止自动续签和补发。

本仓库采用 [MIT License](LICENSE)。PixivDownloader 主程序采用其主仓库声明的独立许可证。
