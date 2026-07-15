from __future__ import annotations

import base64
import ctypes
import json
import os
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from urllib.request import Request, urlopen


AUTH_URL = "https://openapi.baidu.com/oauth/2.0/authorize"
TOKEN_URL = "https://openapi.baidu.com/oauth/2.0/token"
XPAN_FILE_URL = "https://pan.baidu.com/rest/2.0/xpan/file"
XPAN_MEDIA_URL = "https://pan.baidu.com/rest/2.0/xpan/multimedia"
XPAN_NAS_URL = "https://pan.baidu.com/rest/2.0/xpan/nas"
CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Codex" / "baidu-netdisk"
CONFIG_FILE = CONFIG_DIR / "credentials.json"


class DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(data: bytes) -> tuple[DataBlob, Any]:
    buffer = ctypes.create_string_buffer(data)
    return DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def _protect(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("This plugin requires Windows DPAPI and only supports Windows.")
    source, source_buffer = _blob(data)
    target = DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)
    )
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


def _unprotect(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("This plugin requires Windows DPAPI and only supports Windows.")
    source, source_buffer = _blob(data)
    target = DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)
    )
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(target.pbData)


def _seal(value: str) -> str:
    return base64.b64encode(_protect(value.encode("utf-8"))).decode("ascii")


def _open(value: str) -> str:
    return _unprotect(base64.b64decode(value)).decode("utf-8")


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("本机百度网盘配置无法读取，请重新运行授权设置。") from exc


def save_client(app_key: str, app_secret: str, redirect_uri: str = "oob") -> None:
    app_key = app_key.strip()
    app_secret = app_secret.strip()
    redirect_uri = redirect_uri.strip() or "oob"
    if not app_key or not app_secret:
        raise ValueError("App Key 和 Secret Key 不能为空。")
    config = load_config()
    if config.get("app_key") != app_key:
        config.pop("access_token", None)
        config.pop("refresh_token", None)
        config.pop("expires_at", None)
    config.update(
        {
            "app_key": app_key,
            "app_secret": _seal(app_secret),
            "redirect_uri": redirect_uri,
        }
    )
    _write_config(config)


def _write_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temp = CONFIG_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, CONFIG_FILE)


def client_values() -> tuple[str, str, str]:
    config = load_config()
    try:
        return (
            str(config["app_key"]),
            _open(str(config["app_secret"])),
            str(config.get("redirect_uri") or "oob"),
        )
    except (KeyError, ValueError, OSError) as exc:
        raise RuntimeError("尚未配置百度开放平台 App Key 和 Secret Key。") from exc


def authorization_url() -> str:
    app_key, _, redirect_uri = client_values()
    return AUTH_URL + "?" + urlencode(
        {
            "response_type": "code",
            "client_id": app_key,
            "redirect_uri": redirect_uri,
            "scope": "basic,netdisk",
            "display": "tv",
            "qrcode": "1",
            "force_login": "1",
        }
    )


def _request_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params, doseq=True)
    body = urlencode(data, doseq=True).encode("utf-8") if data is not None else None
    for attempt in range(3):
        request = Request(
            url,
            data=body,
            headers={"User-Agent": "Codex-Baidu-Netdisk/0.1", "Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8", errors="replace")
            break
        except HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(_safe_http_error(exc.code, payload)) from exc
        except (URLError, TimeoutError) as exc:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            reason = getattr(exc, "reason", exc)
            raise RuntimeError(f"无法连接百度服务：{reason}") from exc
    try:
        result = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("百度服务返回了无法解析的响应。") from exc
    if not isinstance(result, dict):
        raise RuntimeError("百度服务返回了意外的数据格式。")
    return result


def _safe_http_error(status: int, payload: str) -> str:
    try:
        data = json.loads(payload)
        message = data.get("error_description") or data.get("error_msg") or data.get("error")
    except json.JSONDecodeError:
        message = None
    return f"百度服务请求失败（HTTP {status}）" + (f"：{message}" if message else "。")


def exchange_code(code: str) -> dict[str, Any]:
    app_key, app_secret, redirect_uri = client_values()
    result = _request_json(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code.strip(),
            "client_id": app_key,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
        },
    )
    _store_tokens(result)
    return auth_status()


def _store_tokens(result: dict[str, Any]) -> None:
    access_token = result.get("access_token")
    if not access_token:
        message = result.get("error_description") or result.get("error") or "授权失败"
        raise RuntimeError(f"百度 OAuth 授权失败：{message}")
    config = load_config()
    config["access_token"] = _seal(str(access_token))
    if result.get("refresh_token"):
        config["refresh_token"] = _seal(str(result["refresh_token"]))
    config["expires_at"] = int(time.time()) + int(result.get("expires_in", 2592000))
    _write_config(config)


def _refresh_access_token() -> str:
    config = load_config()
    if not config.get("refresh_token"):
        raise RuntimeError("授权已过期且没有刷新令牌，请重新运行授权设置。")
    app_key, app_secret, _ = client_values()
    result = _request_json(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": _open(str(config["refresh_token"])),
            "client_id": app_key,
            "client_secret": app_secret,
        },
    )
    _store_tokens(result)
    return _open(str(load_config()["access_token"]))


def access_token() -> str:
    config = load_config()
    if not config.get("access_token"):
        raise RuntimeError("百度网盘尚未授权，请先打开 OAuth 设置。")
    if int(config.get("expires_at", 0)) <= int(time.time()) + 120:
        return _refresh_access_token()
    return _open(str(config["access_token"]))


def auth_status() -> dict[str, Any]:
    config = load_config()
    configured = bool(config.get("app_key") and config.get("app_secret"))
    authorized = bool(config.get("access_token"))
    expires_at = int(config.get("expires_at", 0)) if authorized else 0
    return {
        "configured": configured,
        "authorized": authorized,
        "app_key_suffix": str(config.get("app_key", ""))[-4:] if configured else "",
        "expires_at": expires_at or None,
        "expired": bool(authorized and expires_at <= int(time.time())),
        "config_file": str(CONFIG_FILE),
    }


def api_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    request_params = dict(params)
    request_params["access_token"] = access_token()
    result = _request_json(url, params=request_params)
    errno = result.get("errno", result.get("error_code", 0))
    if errno not in (None, 0, "0"):
        message = result.get("errmsg") or result.get("error_msg") or "未知错误"
        raise RuntimeError(f"百度网盘 API 错误 {errno}：{message}")
    return result


def list_files(directory: str = "/", start: int = 0, limit: int = 100) -> list[dict[str, Any]]:
    result = api_json(
        XPAN_FILE_URL,
        {
            "method": "list",
            "dir": directory or "/",
            "start": max(0, int(start)),
            "limit": max(1, min(1000, int(limit))),
            "order": "name",
            "desc": 0,
            "folder": 0,
            "showempty": 0,
        },
    )
    return [_public_file(item) for item in result.get("list", [])]


def search_files(
    keyword: str,
    directory: str = "/",
    recursion: bool = True,
    page: int = 1,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not keyword.strip():
        raise ValueError("搜索关键词不能为空。")
    result = api_json(
        XPAN_FILE_URL,
        {
            "method": "search",
            "key": keyword.strip(),
            "dir": directory or "/",
            "recursion": 1 if recursion else 0,
            "page": max(1, int(page)),
            "num": max(1, min(1000, int(limit))),
        },
    )
    return [_public_file(item) for item in result.get("list", [])]


def user_info() -> dict[str, Any]:
    result = api_json(XPAN_NAS_URL, {"method": "uinfo"})
    allowed = ("baidu_name", "netdisk_name", "vip_type", "uk")
    return {key: result.get(key) for key in allowed if key in result}


def _public_file(item: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "fs_id",
        "path",
        "server_filename",
        "size",
        "isdir",
        "server_ctime",
        "server_mtime",
        "md5",
        "category",
    )
    return {key: item.get(key) for key in allowed if key in item}


def file_metas(fs_ids: list[int]) -> list[dict[str, Any]]:
    clean_ids = [int(value) for value in fs_ids]
    if not clean_ids or len(clean_ids) > 100:
        raise ValueError("一次需要提供 1 到 100 个 fs_id。")
    result = api_json(
        XPAN_MEDIA_URL,
        {"method": "filemetas", "fsids": json.dumps(clean_ids), "dlink": 1, "thumb": 0},
    )
    return list(result.get("list", []))


def _with_token(url: str, token: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault("access_token", token)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _filename(meta: dict[str, Any]) -> str:
    name = str(meta.get("server_filename") or Path(str(meta.get("path", "file"))).name)
    for char in '<>:"/\\|?*':
        name = name.replace(char, "_")
    return name.strip(" .") or f"baidu-{meta.get('fs_id', 'file')}"


def download_files(
    fs_ids: list[int], destination_dir: str, overwrite: bool = False
) -> list[dict[str, Any]]:
    destination = Path(destination_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    token = access_token()
    outputs: list[dict[str, Any]] = []
    for meta in file_metas(fs_ids):
        if int(meta.get("isdir", 0)):
            outputs.append({"fs_id": meta.get("fs_id"), "status": "skipped", "reason": "directory"})
            continue
        dlink = meta.get("dlink")
        if not dlink:
            outputs.append({"fs_id": meta.get("fs_id"), "status": "failed", "reason": "missing dlink"})
            continue
        target = destination / _filename(meta)
        if target.exists() and not overwrite:
            outputs.append({"fs_id": meta.get("fs_id"), "status": "skipped", "path": str(target)})
            continue
        partial = target.with_name(target.name + ".part")
        for attempt in range(3):
            request = Request(
                _with_token(str(dlink), token),
                headers={"User-Agent": "pan.baidu.com", "Accept": "*/*"},
            )
            try:
                partial.unlink(missing_ok=True)
                with urlopen(request, timeout=60) as response, partial.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                expected_size = int(meta.get("size", 0))
                actual_size = partial.stat().st_size
                if expected_size and actual_size != expected_size:
                    raise OSError(f"download size mismatch: {actual_size} != {expected_size}")
                os.replace(partial, target)
                outputs.append(
                    {
                        "fs_id": meta.get("fs_id"),
                        "status": "downloaded",
                        "path": str(target),
                        "size": actual_size,
                    }
                )
                break
            except (HTTPError, URLError, OSError, TimeoutError) as exc:
                partial.unlink(missing_ok=True)
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                outputs.append(
                    {
                        "fs_id": meta.get("fs_id"),
                        "status": "failed",
                        "reason": type(exc).__name__,
                    }
                )
    return outputs
