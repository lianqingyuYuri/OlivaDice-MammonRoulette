"""恶魔轮盘 MammonRoulette 插件的契约测试。

这些测试只覆盖插件的公开入口，业务分支应由使用者随实现一起补充：
- app.json 的命名空间、版本、优先级、消息模式与菜单声明；
- 包级元数据（名称 / 版本 / svn）；
- main.Event 的常用回调；
- 基于 CommandRegistry 的指令注册表。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import MammonRoulette
from MammonRoulette.Core.registry import command

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "MammonRoulette"
NAMESPACE = "MammonRoulette"


def _load_manifest():
    return json.loads((PLUGIN_ROOT / "app.json").read_text(encoding="utf-8"))


def test_manifest_exposes_namespace_version_and_priority():
    manifest = _load_manifest()
    assert manifest["namespace"] == NAMESPACE
    assert manifest["version"] == "2.19.0"
    assert manifest["priority"] == 50000
    assert manifest["message_mode"] == "old_string"
    assert manifest["support"]


def test_manifest_declares_menu_config_without_webui():
    manifest = _load_manifest()
    events = {entry["event"] for entry in manifest["menu_config"]}
    assert events == {
        "MammonRoulette_Menu_main_enabled",
        "MammonRoulette_Menu_poke_enabled",
        "MammonRoulette_Menu_debug",
        "MammonRoulette_Menu_clear_cache",
        "MammonRoulette_Menu_config_reload",
        "MammonRoulette_Menu_manage",
    }
    assert "webui_config" not in manifest
    assert not (PLUGIN_ROOT / "webui").exists()


def test_package_metadata_is_exposed():
    assert MammonRoulette.MammonRoulette_name == "恶魔轮盘"
    assert MammonRoulette.MammonRoulette_ver == "2.19.0"
    assert MammonRoulette.MammonRoulette_svn == 61


def test_event_contract_exposes_common_callbacks():
    for name in ("init", "init_after", "private_message", "group_message", "poke", "save", "menu"):
        assert callable(getattr(MammonRoulette.main.Event, name, None))


def test_command_registry_registers_commands():
    entries = command.entries()
    assert len(entries) >= 10
    names = {entry.name for entry in entries}
    for expected in ("signed", "card", "surrender", "shoot", "join_game", "exit_game", "situation"):
        assert expected in names


def test_command_registry_matches_surrender_by_state():
    event = SimpleNamespace(val={"state": "play"}, msg="投降")
    handler, groups = command.search(event)
    assert handler is not None
    assert handler.__name__ == "surrender"
    assert groups == ()


def test_command_registry_matches_shoot_with_groups():
    event = SimpleNamespace(val={"state": "play"}, msg="开枪")
    handler, groups = command.search(event)
    assert handler is not None
    assert handler.__name__ == "shoot"
    assert groups == ("开", "")


def test_command_registry_ignores_wrong_state():
    event = SimpleNamespace(val={"state": "ob"}, msg="投降")
    assert command.search(event) == (None, None)
