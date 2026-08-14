# PixivDownloader Remote Content

[English](README_en.md)

本仓库保存 [Sywyar/PixivDownloader](https://github.com/Sywyar/PixivDownloader) 面向管理员发布的远程静态内容，目前包括公告正文与公告索引。内容由 GitHub Pages 直接发布，不包含服务端程序或动态构建步骤。

## 公告地址

- 索引：`https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json`
- 索引签名：`https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/index.json.sig`
- 正文：`https://sywyar.github.io/PixivDownloader-Remote-Content/announcements/<message-id>/<locale>.html`
- 源文件：`master` 分支的 `announcements/<message-id>/<locale>.html`

语言使用规范化 BCP 47 tag，例如 `zh-CN`、`en-US`。客户端从索引选择目标语言；缺失时按应用自己的 locale 回退规则处理。

## 发布与安全边界

- GitHub Pages 应配置为从 `master` 分支仓库根目录发布，并强制 HTTPS。
- `master` 应启用分支保护，并将 `Content validation / validate` 设为必需检查。
- 公告索引原始字节使用官方 Ed25519 信任根签名。客户端在解析前验签，并拒绝过期或序列回退的索引；每份正文还必须匹配索引中的 SHA-256。
- 索引最长有效 31 天。续期或修改索引时必须递增 `sequence`，更新有效期及正文摘要，并在全部内容定稿后由维护者使用受保护的签名密钥重新生成 detached 签名。轮换签名密钥时，应先在客户端发布新的信任根。
- 已发布的公告正文和既有语言元数据不可修改或删除；修订内容时创建新的 `message-id`。可以为已有公告追加新的语言。
- HTML 只能使用仓库校验器允许的静态标签、内联 CSS 和受控 HTTPS 链接；禁止脚本、事件属性、表单、iframe、图片、字体及其它外部资源。
- 不得提交凭据、个人信息、用户数据或任何需要访问控制的内容。本仓库及 GitHub Pages 上的全部内容均视为公开信息。

新增或翻译公告前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题请按 [SECURITY.md](SECURITY.md) 私下报告。运行本地校验：

```bash
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_content.py
```

本仓库采用 [MIT License](LICENSE)。PixivDownloader 主程序采用其主仓库声明的独立许可证。
