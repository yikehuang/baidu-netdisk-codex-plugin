from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "baidu-netdisk"
SCRIPTS = PLUGIN / "scripts"
sys.path.insert(0, str(SCRIPTS))

import baidu_auth  # noqa: E402
import server  # noqa: E402


class PluginTests(unittest.TestCase):
    def test_manifests_are_portable(self) -> None:
        plugin = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )

        self.assertEqual(plugin["name"], "baidu-netdisk")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertNotIn("skills", plugin)
        self.assertEqual(mcp["mcpServers"]["baidu-netdisk"]["command"], "cmd.exe")
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/baidu-netdisk")

        for path in ROOT.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".json", ".py", ".cmd", ".md"}:
                self.assertNotIn("C:\\Users\\", path.read_text(encoding="utf-8"), str(path))

    def test_bilingual_release_metadata(self) -> None:
        plugin = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )

        self.assertIn("百度网盘", plugin["interface"]["displayName"])
        self.assertTrue(any("百度网盘" in prompt for prompt in plugin["interface"]["defaultPrompt"]))
        self.assertIn("百度网盘", marketplace["interface"]["displayName"])
        self.assertTrue((ROOT / "CHANGELOG.md").is_file())
        self.assertTrue((ROOT / "releases" / "v0.1.0.md").is_file())
        self.assertTrue((ROOT / "scripts" / "package_plugin.ps1").is_file())

    def test_tool_contract(self) -> None:
        names = [tool["name"] for tool in server.TOOLS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            names,
            [
                "baidu_auth_status",
                "baidu_open_oauth_setup",
                "baidu_user_info",
                "baidu_list_files",
                "baidu_search_files",
                "baidu_download_files",
            ],
        )
        response = server._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(len(response["result"]["tools"]), 6)

    def test_download_filename_is_sanitized(self) -> None:
        value = baidu_auth._filename({"server_filename": 'a<b>:c/d\\e|f?g*.mp3'})
        self.assertEqual(value, "a_b__c_d_e_f_g_.mp3")

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI test")
    def test_dpapi_round_trip(self) -> None:
        secret = "test-only-secret"
        sealed = baidu_auth._seal(secret)
        self.assertNotEqual(sealed, secret)
        self.assertEqual(baidu_auth._open(sealed), secret)


if __name__ == "__main__":
    unittest.main()
