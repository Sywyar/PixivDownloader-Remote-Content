# 安全策略 / Security Policy

PixivDownloader 客户端验证本仓库的 Ed25519 签名索引后，在受限沙箱 iframe 中渲染静态公告 HTML。若发现任何可绕过签名/摘要校验、逃逸 iframe 沙箱、注入未授权外部资源或泄露签名密钥的问题，请私密报告。

## 私密报告方式

请通过本仓库的 [GitHub Private Vulnerability Reporting](https://github.com/Sywyar/PixivDownloader-Remote-Content/security/advisories/new) 或 [PixivDownloader 主仓库私密报告入口](https://github.com/Sywyar/PixivDownloader/security/advisories/new) 提交，切勿在公开 Issue 中发布利用代码、恶意 HTML 样本或凭据。报告请附上受影响的文件路径或 commit、客户端版本、复现步骤与影响范围。

常规内容校验器禁止删除或覆写已发布的公告文件；若安全响应需要撤下某条已发布公告或轮换信任根，维护者需在私密报告中协调客户端与仓库的显式处置流程，不能直接静默替换同名 HTML。

## English summary

PixivDownloader verifies this repository's signed index and renders announcement HTML inside a sandboxed iframe. Report any signature/validation bypass, sandbox escape, unauthorized resource loading, or key exposure privately via [GitHub Private Vulnerability Reporting](https://github.com/Sywyar/PixivDownloader-Remote-Content/security/advisories/new) or the [PixivDownloader main repository advisory form](https://github.com/Sywyar/PixivDownloader/security/advisories/new). Do not post these reports in public Issues. Include the affected path or commit, client version, impact, and minimal reproduction.

Normal validation rejects removal or replacement of published announcements. If a security response requires withdrawal or trust-root rotation, maintainers must privately coordinate explicit client and repository changes rather than silently replacing the same HTML file.
