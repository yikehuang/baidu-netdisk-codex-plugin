# Baidu Netdisk Plugin for Codex / 百度网盘 Codex 插件

[English](#english) | [中文](#中文)

An unofficial, Windows-only plugin for Codex and the ChatGPT desktop app. It uses Baidu's official OAuth and XPan APIs to list, search, and download files from an authorized Baidu Netdisk account.

一个适用于 Codex 和 ChatGPT 桌面版的非官方 Windows 插件。它通过百度官方 OAuth 与 XPan API，列出、搜索并下载用户已授权的百度网盘文件。

This project is not affiliated with or endorsed by Baidu or OpenAI.

本项目与百度或 OpenAI 无隶属关系，也未获得其官方背书。

## English

### Features

- Check local OAuth authorization status without exposing tokens.
- Read basic information for the authorized account.
- List files and folders in a Netdisk directory.
- Search the authorized user's Netdisk recursively.
- Download selected files by `fs_id`.
- Encrypt the Baidu App Secret and OAuth tokens with Windows DPAPI.

The plugin intentionally does not upload, delete, move, rename, publish, or share files.

### Requirements

- Windows 10 or newer.
- Python 3.10 or newer, including Tkinter and the Windows `py` launcher or `python` command.
- Codex or the ChatGPT desktop app with plugin and local MCP support.
- A Baidu Netdisk Open Platform application with an App Key and Secret Key.

### Install from GitHub

```powershell
codex plugin marketplace add yikehuang/baidu-netdisk-codex-plugin
codex plugin add baidu-netdisk@baidu-netdisk-community
```

Restart Codex or the ChatGPT desktop app, then start a new task before using the plugin.

### Install from a release package

Download the ZIP and `.sha256` file from the [latest release](https://github.com/yikehuang/baidu-netdisk-codex-plugin/releases/latest), verify the checksum, and extract it:

```powershell
Get-FileHash .\baidu-netdisk-codex-plugin-v0.1.0.zip -Algorithm SHA256
Get-Content .\baidu-netdisk-codex-plugin-v0.1.0.zip.sha256
Expand-Archive .\baidu-netdisk-codex-plugin-v0.1.0.zip -DestinationPath .\baidu-netdisk-plugin
Set-Location .\baidu-netdisk-plugin\baidu-netdisk-codex-plugin-v0.1.0
codex plugin marketplace add .
codex plugin add baidu-netdisk@baidu-netdisk-community
```

The hash printed by `Get-FileHash` must match the value in the `.sha256` file.

### First-time authorization

1. Create an application in the [Baidu Netdisk Open Platform](https://yun.baidu.com/open/platform).
2. In a new Codex or ChatGPT desktop task, ask the agent to run `baidu_open_oauth_setup`.
3. Enter the App Key, Secret Key, and redirect URI in the local setup window.
4. Open the authorization URL, approve access, and paste the authorization code into the setup window.
5. Run `baidu_auth_status` to confirm that authorization succeeded.

Credentials are stored in `%LOCALAPPDATA%\Codex\baidu-netdisk\credentials.json`. The App Key is stored as plain configuration; the Secret Key, access token, and refresh token are encrypted with Windows DPAPI for the current Windows user.

### Available tools

| Tool | Purpose |
| --- | --- |
| `baidu_auth_status` | Check whether OAuth is configured and authorized. |
| `baidu_open_oauth_setup` | Open the local OAuth setup window. |
| `baidu_user_info` | Read basic account information. |
| `baidu_list_files` | List a directory in the authorized account. |
| `baidu_search_files` | Search the authorized account. |
| `baidu_download_files` | Download up to 100 selected files by `fs_id`. |

### Public share links

This plugin does not bypass Baidu share pages, extraction codes, CAPTCHA, membership restrictions, rate limits, or safety checks. Public share-link APIs are not available to ordinary personal developers. Save shared files to your own Netdisk first, then search or download them through this plugin.

## 中文

### 功能

- 检查本地 OAuth 授权状态，不暴露令牌。
- 读取已授权账号的基本信息。
- 列出网盘目录中的文件和文件夹。
- 递归搜索已授权用户的百度网盘。
- 按 `fs_id` 下载选中的文件。
- 使用 Windows DPAPI 加密百度应用 Secret Key 和 OAuth 令牌。

插件有意限制为读取和下载，不会上传、删除、移动、重命名、公开或分享文件。

### 环境要求

- Windows 10 或更高版本。
- Python 3.10 或更高版本，需包含 Tkinter，并可使用 Windows `py` 启动器或 `python` 命令。
- 支持插件和本地 MCP 的 Codex 或 ChatGPT 桌面版。
- 一个包含 App Key 和 Secret Key 的百度网盘开放平台应用。

### 从 GitHub 安装

```powershell
codex plugin marketplace add yikehuang/baidu-netdisk-codex-plugin
codex plugin add baidu-netdisk@baidu-netdisk-community
```

重启 Codex 或 ChatGPT 桌面版，然后新建一个任务再使用插件。

### 从 Release 安装包安装

从[最新 Release](https://github.com/yikehuang/baidu-netdisk-codex-plugin/releases/latest)下载 ZIP 和 `.sha256` 文件，核对校验值后解压：

```powershell
Get-FileHash .\baidu-netdisk-codex-plugin-v0.1.0.zip -Algorithm SHA256
Get-Content .\baidu-netdisk-codex-plugin-v0.1.0.zip.sha256
Expand-Archive .\baidu-netdisk-codex-plugin-v0.1.0.zip -DestinationPath .\baidu-netdisk-plugin
Set-Location .\baidu-netdisk-plugin\baidu-netdisk-codex-plugin-v0.1.0
codex plugin marketplace add .
codex plugin add baidu-netdisk@baidu-netdisk-community
```

`Get-FileHash` 显示的哈希值必须与 `.sha256` 文件中的值一致。

### 首次授权

1. 在[百度网盘开放平台](https://yun.baidu.com/open/platform)创建应用。
2. 在新的 Codex 或 ChatGPT 桌面版任务中，让智能体运行 `baidu_open_oauth_setup`。
3. 在本地设置窗口中输入 App Key、Secret Key 和回调地址。
4. 打开授权网址并同意授权，然后把授权码粘贴到设置窗口。
5. 运行 `baidu_auth_status`，确认授权成功。

凭据保存在 `%LOCALAPPDATA%\Codex\baidu-netdisk\credentials.json`。App Key 作为普通配置保存；Secret Key、访问令牌和刷新令牌使用 Windows DPAPI 加密，并且只能由当前 Windows 用户解密。

### 可用工具

| 工具 | 用途 |
| --- | --- |
| `baidu_auth_status` | 检查 OAuth 是否已配置和授权。 |
| `baidu_open_oauth_setup` | 打开本地 OAuth 设置窗口。 |
| `baidu_user_info` | 读取账号基本信息。 |
| `baidu_list_files` | 列出已授权账号中的目录。 |
| `baidu_search_files` | 搜索已授权账号。 |
| `baidu_download_files` | 按 `fs_id` 下载最多 100 个选中的文件。 |

### 百度网盘公开分享链接

本插件不会绕过百度分享页、提取码、验证码、会员限制、频率限制或安全检查。普通个人开发者无法使用公开分享链接 API。请先把分享文件保存到自己的百度网盘，再通过本插件搜索或下载。

## Development / 开发

The MCP server uses only the Python standard library. MCP 服务端仅使用 Python 标准库。

```powershell
py -3 -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\package_plugin.ps1 -Version 0.1.0 -OutputDirectory dist
```

The installable plugin lives under `plugins/baidu-netdisk`. The repository-level marketplace manifest is at `.agents/plugins/marketplace.json`.

可安装插件位于 `plugins/baidu-netdisk`，仓库级 marketplace 清单位于 `.agents/plugins/marketplace.json`。

See [SECURITY.md](SECURITY.md) for security reporting and [CHANGELOG.md](CHANGELOG.md) for release history.

安全问题报告方式见 [SECURITY.md](SECURITY.md)，版本记录见 [CHANGELOG.md](CHANGELOG.md)。

## License / 许可证

[MIT](LICENSE)
