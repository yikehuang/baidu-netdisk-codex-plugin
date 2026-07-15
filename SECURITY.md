# Security Policy / 安全政策

## English

### Supported versions

Security fixes are applied to the latest release on the default branch.

### Report a vulnerability

Use GitHub's private vulnerability reporting or open a private security advisory for this repository. Do not include App Keys, Secret Keys, OAuth tokens, authorization codes, private filenames, or private Netdisk paths in a public issue.

### Credential handling

The plugin stores its local configuration outside the repository at `%LOCALAPPDATA%\Codex\baidu-netdisk\credentials.json`. The Baidu App Secret and OAuth tokens are encrypted with Windows DPAPI for the current Windows user. The plugin refuses to run its credential encryption functions on non-Windows systems.

Revoke the Baidu application authorization and replace the application credentials if you believe a secret or token was exposed.

## 中文

### 支持的版本

安全修复会应用到默认分支上的最新版本。

### 报告安全漏洞

请使用 GitHub 私密漏洞报告或为本仓库创建私密安全公告。不要在公开 Issue 中提交 App Key、Secret Key、OAuth 令牌、授权码、私密文件名或私密网盘路径。

### 凭据处理

插件把本地配置保存在仓库外的 `%LOCALAPPDATA%\Codex\baidu-netdisk\credentials.json`。百度应用 Secret Key 和 OAuth 令牌使用 Windows DPAPI 加密，并且仅限当前 Windows 用户解密。插件拒绝在非 Windows 系统上运行凭据加密功能。

如果你怀疑 Secret Key 或令牌已经泄露，请撤销百度应用授权并更换应用凭据。
