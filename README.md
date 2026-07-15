# Baidu Netdisk plugin for Codex

An unofficial, Windows-only plugin for Codex and the ChatGPT desktop app. It uses Baidu's official OAuth and XPan APIs to list, search, and download files from a user's authorized Baidu Netdisk account.

This project is not affiliated with or endorsed by Baidu or OpenAI.

## Features

- Check local OAuth authorization status without exposing tokens.
- Read basic information for the authorized account.
- List files and folders in a Netdisk directory.
- Search the authorized user's Netdisk recursively.
- Download selected files by `fs_id`.
- Encrypt the Baidu App Secret and OAuth tokens with Windows DPAPI.

The plugin intentionally does not upload, delete, move, rename, publish, or share files.

## Requirements

- Windows 10 or newer.
- Python 3.10 or newer, including Tkinter and the Windows `py` launcher or `python` command.
- Codex or the ChatGPT desktop app with plugin and local MCP support.
- A Baidu Netdisk Open Platform application with an App Key and Secret Key.

## Install from GitHub

```powershell
codex plugin marketplace add yikehuang/baidu-netdisk-codex-plugin
codex plugin add baidu-netdisk@baidu-netdisk-community
```

Restart Codex or the ChatGPT desktop app, then start a new task before using the plugin.

You can also clone the repository and add its root as a local marketplace:

```powershell
git clone https://github.com/yikehuang/baidu-netdisk-codex-plugin.git
codex plugin marketplace add .\baidu-netdisk-codex-plugin
codex plugin add baidu-netdisk@baidu-netdisk-community
```

## First-time authorization

1. Create an application in the [Baidu Netdisk Open Platform](https://yun.baidu.com/open/platform).
2. In a new Codex or ChatGPT desktop task, ask the agent to run `baidu_open_oauth_setup`.
3. Enter the App Key, Secret Key, and redirect URI in the local setup window.
4. Open the authorization URL, approve access, and paste the authorization code into the setup window.
5. Run `baidu_auth_status` to confirm that authorization succeeded.

Credentials are stored in `%LOCALAPPDATA%\Codex\baidu-netdisk\credentials.json`. The App Key is stored as plain configuration; the Secret Key, access token, and refresh token are encrypted with Windows DPAPI for the current Windows user.

## Available tools

| Tool | Purpose |
| --- | --- |
| `baidu_auth_status` | Check whether OAuth is configured and authorized. |
| `baidu_open_oauth_setup` | Open the local OAuth setup window. |
| `baidu_user_info` | Read basic account information. |
| `baidu_list_files` | List a directory in the authorized account. |
| `baidu_search_files` | Search the authorized account. |
| `baidu_download_files` | Download up to 100 selected files by `fs_id`. |

## Public share links

This plugin does not bypass Baidu share pages, extraction codes, CAPTCHA, membership restrictions, rate limits, or safety checks. Public share-link APIs are not available to ordinary personal developers. Save shared files to your own Netdisk first, then search or download them through this plugin.

## Development

The MCP server uses only the Python standard library.

```powershell
py -3 -m unittest discover -s tests -v
```

The installable plugin lives under `plugins/baidu-netdisk`. The repository-level marketplace manifest is at `.agents/plugins/marketplace.json`.

## License

[MIT](LICENSE)
