from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from baidu_auth import auth_status, download_files, list_files, search_files, user_info


SERVER_VERSION = "0.1.0"
SETUP_SCRIPT = Path(__file__).with_name("setup_oauth.py")


TOOLS = [
    {
        "name": "baidu_auth_status",
        "description": "Check whether the local Baidu Netdisk official OAuth connection is configured and authorized. Never returns secrets or tokens.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "baidu_open_oauth_setup",
        "description": "Open the local OAuth setup window. The user enters Baidu App Key, Secret Key, and authorization code directly into the local window.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "baidu_user_info",
        "description": "Return basic information for the currently authorized Baidu Netdisk account.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "baidu_list_files",
        "description": "List files and folders in a directory of the authorized user's Baidu Netdisk.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "default": "/"},
                "start": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "baidu_search_files",
        "description": "Search files in the authorized user's Baidu Netdisk. Public share links must first be saved to the user's own Netdisk.",
        "inputSchema": {
            "type": "object",
            "required": ["keyword"],
            "properties": {
                "keyword": {"type": "string", "minLength": 1},
                "directory": {"type": "string", "default": "/"},
                "recursion": {"type": "boolean", "default": True},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "baidu_download_files",
        "description": "Download up to 100 files by fs_id from the authorized user's Baidu Netdisk to a local directory.",
        "inputSchema": {
            "type": "object",
            "required": ["fs_ids", "destination_dir"],
            "properties": {
                "fs_ids": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 100,
                    "items": {"type": "integer"},
                },
                "destination_dir": {"type": "string", "minLength": 1},
                "overwrite": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
    },
]


def _result(value: Any) -> dict[str, Any]:
    return {
        "content": [
            {"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2, default=str)}
        ]
    }


def _tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "baidu_auth_status":
        return _result(auth_status())
    if name == "baidu_open_oauth_setup":
        subprocess.Popen([sys.executable, str(SETUP_SCRIPT)], close_fds=True)
        return _result({"opened": True, "message": "本地百度 OAuth 设置窗口已打开。"})
    if name == "baidu_user_info":
        return _result(user_info())
    if name == "baidu_list_files":
        return _result(
            list_files(
                arguments.get("directory", "/"),
                arguments.get("start", 0),
                arguments.get("limit", 100),
            )
        )
    if name == "baidu_search_files":
        return _result(
            search_files(
                arguments["keyword"],
                arguments.get("directory", "/"),
                arguments.get("recursion", True),
                arguments.get("page", 1),
                arguments.get("limit", 100),
            )
        )
    if name == "baidu_download_files":
        return _result(
            download_files(
                arguments["fs_ids"],
                arguments["destination_dir"],
                arguments.get("overwrite", False),
            )
        )
    raise ValueError(f"Unknown tool: {name}")


def _handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        requested = message.get("params", {}).get("protocolVersion", "2025-03-26")
        result = {
            "protocolVersion": requested,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "baidu-netdisk", "version": SERVER_VERSION},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params") or {}
        try:
            result = _tool_call(str(params.get("name", "")), params.get("arguments") or {})
        except Exception as exc:
            result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
    elif method == "ping":
        result = {}
    elif method in ("resources/list", "prompts/list"):
        result = {"resources": []} if method == "resources/list" else {"prompts": []}
    elif request_id is None:
        return None
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _read_message() -> dict[str, Any] | None:
    first = sys.stdin.buffer.readline()
    if not first:
        return None
    if first.lower().startswith(b"content-length:"):
        length = int(first.split(b":", 1)[1].strip())
        while True:
            line = sys.stdin.buffer.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        data = sys.stdin.buffer.read(length)
    else:
        data = first.strip()
    if not data:
        return {}
    return json.loads(data.decode("utf-8"))


def main() -> None:
    while True:
        try:
            message = _read_message()
            if message is None:
                break
            response = _handle(message)
            if response is not None:
                payload = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
                sys.stdout.buffer.write(payload.encode("utf-8") + b"\n")
                sys.stdout.buffer.flush()
        except Exception as exc:
            error = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {type(exc).__name__}"},
            }
            sys.stdout.buffer.write(json.dumps(error).encode("utf-8") + b"\n")
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
