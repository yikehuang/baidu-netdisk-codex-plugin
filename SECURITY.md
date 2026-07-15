# Security policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

## Report a vulnerability

Use GitHub's private vulnerability reporting or open a private security advisory for this repository. Do not include App Keys, Secret Keys, OAuth tokens, authorization codes, private filenames, or private Netdisk paths in a public issue.

## Credential handling

The plugin stores its local configuration outside the repository at `%LOCALAPPDATA%\Codex\baidu-netdisk\credentials.json`. The Baidu App Secret and OAuth tokens are encrypted with Windows DPAPI for the current Windows user. The plugin refuses to run its credential encryption functions on non-Windows systems.

Revoke the Baidu application authorization and replace the application credentials if you believe a secret or token was exposed.
