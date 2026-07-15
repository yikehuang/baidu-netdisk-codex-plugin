from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from baidu_auth import auth_status, authorization_url, exchange_code, load_config, save_client


class SetupWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Codex 百度网盘官方 OAuth 设置")
        self.geometry("620x430")
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        self._build()
        self._load()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=22)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="百度网盘官方 OAuth", font=("Microsoft YaHei UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        note = (
            "在百度网盘开放平台创建应用后，将 App Key 和 Secret Key 填在这里。\n"
            "Secret Key、访问令牌会使用 Windows DPAPI 加密，只保存在当前电脑。"
        )
        ttk.Label(frame, text=note, wraplength=560, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 18)
        )

        ttk.Label(frame, text="App Key").grid(row=2, column=0, sticky="w", padx=(0, 12), pady=6)
        self.app_key = ttk.Entry(frame, width=55)
        self.app_key.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Secret Key").grid(row=3, column=0, sticky="w", padx=(0, 12), pady=6)
        self.app_secret = ttk.Entry(frame, width=55, show="*")
        self.app_secret.grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="回调地址").grid(row=4, column=0, sticky="w", padx=(0, 12), pady=6)
        self.redirect_uri = ttk.Entry(frame, width=55)
        self.redirect_uri.grid(row=4, column=1, sticky="ew", pady=6)
        self.redirect_uri.insert(0, "oob")

        ttk.Button(frame, text="保存并打开百度授权页", command=self.open_auth).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(16, 12)
        )

        ttk.Label(frame, text="授权码").grid(row=6, column=0, sticky="w", padx=(0, 12), pady=6)
        self.code = ttk.Entry(frame, width=55)
        self.code.grid(row=6, column=1, sticky="ew", pady=6)

        ttk.Button(frame, text="完成授权", command=self.finish_auth).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(12, 12)
        )
        self.status_label = ttk.Label(frame, text="", wraplength=560)
        self.status_label.grid(row=8, column=0, columnspan=2, sticky="w")

    def _load(self) -> None:
        config = load_config()
        if config.get("app_key"):
            self.app_key.insert(0, str(config["app_key"]))
        if config.get("redirect_uri"):
            self.redirect_uri.delete(0, tk.END)
            self.redirect_uri.insert(0, str(config["redirect_uri"]))
        self._refresh_status()

    def _save(self) -> None:
        secret = self.app_secret.get().strip()
        if not secret:
            existing = load_config()
            if existing.get("app_secret") and existing.get("app_key") == self.app_key.get().strip():
                return
        save_client(self.app_key.get(), secret, self.redirect_uri.get())

    def open_auth(self) -> None:
        try:
            self._save()
            webbrowser.open(authorization_url())
            self.status_label.config(text="授权页已打开。登录并同意授权后，把页面显示的授权码填到下方。")
        except Exception as exc:
            messagebox.showerror("无法打开授权页", str(exc))

    def finish_auth(self) -> None:
        code = self.code.get().strip()
        if not code:
            messagebox.showwarning("缺少授权码", "请先填写百度授权页给出的授权码。")
            return
        try:
            exchange_code(code)
            self.code.delete(0, tk.END)
            self._refresh_status()
            messagebox.showinfo("授权成功", "Codex 已可以通过官方 API 访问你的百度网盘。")
        except Exception as exc:
            messagebox.showerror("授权失败", str(exc))

    def _refresh_status(self) -> None:
        status = auth_status()
        if status["authorized"] and not status["expired"]:
            text = "状态：已授权"
        elif status["authorized"]:
            text = "状态：授权已过期，将在使用时尝试自动刷新"
        elif status["configured"]:
            text = "状态：应用信息已保存，尚未完成授权"
        else:
            text = "状态：尚未配置"
        self.status_label.config(text=text)


if __name__ == "__main__":
    SetupWindow().mainloop()
