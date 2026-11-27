# -*- encoding: utf-8 -*-
"""config.py 与 main.py 的单元测试。"""

import json
import os
from types import SimpleNamespace

import MammonRoulette
import MammonRoulette.main as main
from MammonRoulette import config

from fakes import FakeMsgEvent, FakePluginEvent, add_player, build_game


class FakeProc:
    def __init__(self, bot_info_dict=None):
        self.logs = []
        self.Proc_data = {"bot_info_dict": bot_info_dict or []}

    def log(self, level, msg):
        self.logs.append((level, msg))


def test_config_init_read_save_roundtrip(monkeypatch, tmp_path):
    os.makedirs(tmp_path / "plugin" / "data" / "MammonRoulette", exist_ok=True)
    proc = FakeProc(["unity"])
    config.initConfig(proc)
    assert (tmp_path / "plugin" / "data" / "MammonRoulette" / "config.ini").exists()

    config.readConfig(proc)
    assert "unity" in MammonRoulette.custom.dictModeCustom
    config.saveConfig(proc)
    assert (tmp_path / "plugin" / "data" / "MammonRoulette" / "unity" / "customMode.json").exists()
    assert (tmp_path / "plugin" / "data" / "MammonRoulette" / "unity" / "customProp.json").exists()
    assert (tmp_path / "plugin" / "data" / "MammonRoulette" / "unity" / "customEffect.json").exists()


def test_config_init_skips_when_file_exists(monkeypatch, tmp_path):
    os.makedirs(tmp_path / "plugin" / "data" / "MammonRoulette", exist_ok=True)
    config_file = tmp_path / "plugin" / "data" / "MammonRoulette" / "config.ini"
    config_file.write_text("", encoding="utf-8")
    proc = FakeProc([])
    config.initConfig(proc)
    assert config_file.exists()


def test_config_read_merges_custom_json(monkeypatch, tmp_path):
    os.makedirs(tmp_path / "plugin" / "data" / "MammonRoulette", exist_ok=True)
    config_file = tmp_path / "plugin" / "data" / "MammonRoulette" / "config.ini"
    config_file.write_text("", encoding="utf-8")
    custom_dir = tmp_path / "plugin" / "data" / "MammonRoulette" / "unity"
    os.makedirs(custom_dir, exist_ok=True)
    (custom_dir / "customMode.json").write_text(
        json.dumps({"经典": {"points": 999}}), encoding="utf-8"
    )
    (custom_dir / "customProp.json").write_text(json.dumps({}), encoding="utf-8")
    (custom_dir / "customEffect.json").write_text(json.dumps({}), encoding="utf-8")
    proc = FakeProc(["unity"])
    config.readConfig(proc)
    assert MammonRoulette.custom.dictModeCustom["unity"]["经典"]["points"] == 999


def test_main_unity_enabled(monkeypatch):
    import OlivaDiceCore

    monkeypatch.setattr(OlivaDiceCore.console, "getConsoleSwitchByHash", lambda key, bot_hash: 1)
    assert main.unity_enabled("MrMainEnabled") is True
    assert main.unity_enabled("MrMainEnabled", "bot1") is True

    monkeypatch.setattr(OlivaDiceCore.console, "getConsoleSwitchByHash", lambda key, bot_hash: 1 if bot_hash == "unity" else 0)
    assert main.unity_enabled("MrMainEnabled", "bot1") is False


def test_main_event_save(monkeypatch, tmp_path):
    game_path = tmp_path / "game.json"
    monkeypatch.setattr(MammonRoulette.config, "tmpGameDataPath", str(game_path))
    main.game_data.clear()
    main.game_data["g1"] = {"start": True}
    main.Event.save(None, None)
    data = json.loads(game_path.read_text(encoding="utf-8"))
    assert data["g1"]["start"] is True


def test_main_event_init_pass(monkeypatch):
    main.Event.init(None, None)


def test_main_menu_main_enabled_and_poke(monkeypatch, tmp_path):
    import OlivaDiceCore

    calls = []
    monkeypatch.setattr(OlivaDiceCore.console, "getConsoleSwitchByHash", lambda key, bot_hash: 0)
    monkeypatch.setattr(OlivaDiceCore.console, "setConsoleSwitchByHash", lambda key, value: calls.append((key, value)))
    proc = FakeProc()

    event = SimpleNamespace(
        data=SimpleNamespace(namespace="MammonRoulette", event="MammonRoulette_Menu_main_enabled")
    )
    main.Event.menu(event, proc)
    assert ("MrMainEnabled", 1) in calls

    event.data.event = "MammonRoulette_Menu_poke_enabled"
    main.Event.menu(event, proc)
    assert ("MrPokeEnabled", 1) in calls


def test_main_menu_debug_and_clear_cache(monkeypatch, tmp_path):
    import OlivaDiceCore

    os.makedirs(tmp_path / "plugin" / "data" / "MammonRoulette", exist_ok=True)
    (tmp_path / "plugin" / "data" / "MammonRoulette" / "config.ini").write_text("", encoding="utf-8")
    game_path = tmp_path / "game.json"
    monkeypatch.setattr(MammonRoulette.config, "tmpGameDataPath", str(game_path))
    monkeypatch.setattr(OlivaDiceCore.console, "getConsoleSwitchByHash", lambda key, bot_hash: 1)
    proc = FakeProc()

    event = SimpleNamespace(
        data=SimpleNamespace(namespace="MammonRoulette", event="MammonRoulette_Menu_debug")
    )
    MammonRoulette.config.debug = 0
    main.Event.menu(event, proc)
    assert MammonRoulette.config.debug == 1

    event.data.event = "MammonRoulette_Menu_clear_cache"
    main.game_data["g1"] = {"start": True}
    main.Event.menu(event, proc)
    assert main.game_data == {}


def test_main_menu_config_reload(monkeypatch, tmp_path):
    import OlivaDiceCore

    os.makedirs(tmp_path / "plugin" / "data" / "MammonRoulette", exist_ok=True)
    (tmp_path / "plugin" / "data" / "MammonRoulette" / "config.ini").write_text("", encoding="utf-8")
    monkeypatch.setattr(OlivaDiceCore.console, "getConsoleSwitchByHash", lambda key, bot_hash: 1)
    proc = FakeProc(["unity"])
    event = SimpleNamespace(
        data=SimpleNamespace(namespace="MammonRoulette", event="MammonRoulette_Menu_config_reload")
    )
    main.Event.menu(event, proc)
    assert any("重加载" in str(log) for _, log in proc.logs)


def test_unity_reply_skips_when_not_allowed():
    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="局势", allow_reply=False)
    plugin_event = FakePluginEvent(plugin_info={"func_type": "group_message"})
    main.unity_reply(plugin_event, None, msg_event)
    assert not plugin_event.replies


def test_unity_reply_group_situation(monkeypatch):
    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["start"] = True
    game["data"].update({"shooter": "u1", "ammo_live": 1, "ammo_blank": 1, "bullet": False})
    main.game_data.clear()
    main.game_data["g1"] = game

    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="局势", allow_reply=True)
    plugin_event = FakePluginEvent(plugin_info={"func_type": "group_message"})
    main.unity_reply(plugin_event, None, msg_event)
    assert plugin_event.replies


def test_unity_reply_poke_selects_message(monkeypatch):
    import MammonRoulette

    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    monkeypatch.setattr(MammonRoulette.command, "search", lambda msg_event: (None, None))
    main.game_data.clear()
    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="", allow_reply=True)
    plugin_event = FakePluginEvent(
        plugin_info={"func_type": "poke"},
        data=SimpleNamespace(target_id="bot", message="", sender={}, extend={}, group_id="g1", user_id="u1"),
        base_info={"self_id": "bot"},
    )
    main.unity_reply(plugin_event, None, msg_event)
    assert msg_event.msg == "加入"
    assert not plugin_event.replies


def test_unity_reply_debug_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(MammonRoulette.config, "debug", 1)
    data_path = tmp_path / "data.json"
    monkeypatch.setattr(MammonRoulette.config, "tmpGameDataPath", str(data_path))
    monkeypatch.setattr(MammonRoulette.command, "search", lambda msg_event: (None, None))

    game = build_game("经典")
    add_player(game, "u1", hp=4)
    add_player(game, "u2", hp=4)
    game["start"] = True
    data_path.write_text(json.dumps({"g1": game}), encoding="utf-8")

    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="x", allow_reply=True)
    plugin_event = FakePluginEvent(plugin_info={"func_type": "group_message"})
    proc = FakeProc()
    main.unity_reply(plugin_event, proc, msg_event)
    assert proc.logs
    assert "g1" in json.loads(data_path.read_text(encoding="utf-8"))


def test_unity_reply_private_branch(monkeypatch):
    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    monkeypatch.setattr(MammonRoulette.command, "search", lambda msg_event: (None, None))
    main.game_data.clear()
    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id=None, msg="x", allow_reply=True)
    plugin_event = FakePluginEvent(plugin_info={"func_type": "private_message"})
    main.unity_reply(plugin_event, None, msg_event)
    assert msg_event.val["state"] == "priv"
    assert not plugin_event.replies


def test_unity_reply_poke_state_branches(monkeypatch):
    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    monkeypatch.setattr(MammonRoulette.command, "search", lambda msg_event: (None, None))
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    add_player(game, "u2", hp=4)
    main.game_data.clear()
    main.game_data["g1"] = game

    def poke_event(target_id):
        return FakePluginEvent(
            plugin_info={"func_type": "poke"},
            data=SimpleNamespace(target_id=target_id, message="", sender={}, extend={}, group_id="g1", user_id="u1"),
            base_info={"self_id": "bot"},
        )

    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="", allow_reply=True)
    main.unity_reply(poke_event("bot"), None, msg_event)
    assert msg_event.msg == "退出"

    game["start"] = True
    game["data"]["shooter"] = "u1"
    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="", allow_reply=True)
    main.unity_reply(poke_event("bot"), None, msg_event)
    assert msg_event.msg == "局势"

    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="", allow_reply=True)
    main.unity_reply(poke_event("u2"), None, msg_event)
    assert msg_event.msg == "开枪u2"


def test_unity_reply_poke_no_message(monkeypatch):
    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    monkeypatch.setattr(MammonRoulette.command, "search", lambda msg_event: (None, None))
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    main.game_data.clear()
    main.game_data["g1"] = game
    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="", allow_reply=True)
    plugin_event = FakePluginEvent(
        plugin_info={"func_type": "poke"},
        data=SimpleNamespace(target_id="u2", message="", sender={}, extend={}, group_id="g1", user_id="u1"),
        base_info={"self_id": "bot"},
    )
    main.unity_reply(plugin_event, None, msg_event)
    assert msg_event.msg == ""
    assert not plugin_event.replies


def test_unity_reply_clears_over_game(roulette_db, monkeypatch):
    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["start"] = True
    game["data"].update({"shooter": "u1", "ammo_live": 1, "ammo_blank": 1, "bullet": False})
    main.game_data.clear()
    main.game_data["g1"] = game
    msg_event = FakeMsgEvent(val={}, user_id="u1", group_id="g1", msg="投降", allow_reply=True)
    plugin_event = FakePluginEvent(plugin_info={"func_type": "group_message"})
    main.unity_reply(plugin_event, None, msg_event)
    assert main.game_data["g1"] == {}


def test_unity_reply_bot_action_branch(monkeypatch):
    monkeypatch.setattr(MammonRoulette.config, "debug", 0)
    monkeypatch.setattr(MammonRoulette.Core.registry.botReg, "action", lambda msg_event: None)
    game = build_game("经典")
    add_player(game, "bot_1", hp=4, actions=1, bot_model="达尔文")
    add_player(game, "u2", hp=4, actions=0)
    game["start"] = True
    game["data"].update({"shooter": "bot_1", "ammo_live": 1, "ammo_blank": 1, "bullet": False})
    main.game_data.clear()
    main.game_data["g1"] = game
    msg_event = FakeMsgEvent(val={}, user_id="bot_1", group_id="g1", msg="局势", allow_reply=True)
    plugin_event = FakePluginEvent(plugin_info={"func_type": "group_message"})
    main.unity_reply(plugin_event, None, msg_event)
    assert plugin_event.replies


def test_event_poke_returns_early(monkeypatch):
    monkeypatch.setattr(main, "unity_enabled", lambda *a, **k: False)
    plugin_event = SimpleNamespace(
        bot_info=SimpleNamespace(hash="bot"),
        data=SimpleNamespace(group_id="g1"),
    )
    main.Event.poke(plugin_event, None)


def test_event_init_after_loads_existing_game_data(monkeypatch, tmp_path):
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps({"g1": {"start": True}}), encoding="utf-8")
    monkeypatch.setattr(MammonRoulette.config, "tmpGameDataPath", str(data_path))
    monkeypatch.setattr(MammonRoulette.config, "initConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.config, "readConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.config, "saveConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.Core.registry, "init_after", lambda: None)
    monkeypatch.setattr(main, "initCustom", lambda *a: None)
    monkeypatch.setattr(main, "readCustom", lambda *a: None)
    monkeypatch.setattr(main, "saveCustom", lambda *a: None)
    monkeypatch.setattr(main, "loadCustomInto", lambda *a: None)

    created = []

    class FakeDB:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def create(self, name, *args, **kwargs):
            created.append(name)

    monkeypatch.setattr(main, "DataBase", FakeDB)
    main.game_data.clear()
    main.Event.init_after(None, FakeProc())
    assert main.game_data == {"g1": {"start": True}}
    assert set(created) == {"gambler", "bot"}


def test_event_init_after_creates_missing_file(monkeypatch, tmp_path):
    data_path = tmp_path / "data.json"
    monkeypatch.setattr(MammonRoulette.config, "tmpGameDataPath", str(data_path))
    monkeypatch.setattr(MammonRoulette.config, "initConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.config, "readConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.config, "saveConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.Core.registry, "init_after", lambda: None)
    monkeypatch.setattr(main, "initCustom", lambda *a: None)
    monkeypatch.setattr(main, "readCustom", lambda *a: None)
    monkeypatch.setattr(main, "saveCustom", lambda *a: None)
    monkeypatch.setattr(main, "loadCustomInto", lambda *a: None)

    class FakeDB:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def create(self, name, *args, **kwargs):
            pass

    monkeypatch.setattr(main, "DataBase", FakeDB)
    proc = FakeProc()
    main.Event.init_after(None, proc)
    assert json.loads(data_path.read_text(encoding="utf-8")) == {}
    assert any("不存在" in str(log) for _, log in proc.logs)


def test_event_init_after_load_error(monkeypatch, tmp_path):
    bad_path = tmp_path / "data.json"
    bad_path.mkdir()
    monkeypatch.setattr(MammonRoulette.config, "tmpGameDataPath", str(bad_path))
    monkeypatch.setattr(MammonRoulette.config, "initConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.config, "readConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.config, "saveConfig", lambda Proc: None)
    monkeypatch.setattr(MammonRoulette.Core.registry, "init_after", lambda: None)
    monkeypatch.setattr(main, "initCustom", lambda *a: None)
    monkeypatch.setattr(main, "readCustom", lambda *a: None)
    monkeypatch.setattr(main, "saveCustom", lambda *a: None)
    monkeypatch.setattr(main, "loadCustomInto", lambda *a: None)

    class FakeDB:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def create(self, name, *args, **kwargs):
            pass

    monkeypatch.setattr(main, "DataBase", FakeDB)
    proc = FakeProc()
    main.Event.init_after(None, proc)
    assert any("丢失" in str(log) for _, log in proc.logs)


def test_event_group_and_private_message_wiring(monkeypatch):
    monkeypatch.setattr(main, "unity_enabled", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(main, "MsgEvent", lambda event: "MSG")
    monkeypatch.setattr(main, "unity_reply", lambda plugin_event, proc, msg_event: calls.append(msg_event))
    event = SimpleNamespace(bot_info=SimpleNamespace(hash="bot"))
    main.Event.group_message(event, None)
    main.Event.private_message(event, None)
    assert calls == ["MSG", "MSG"]


def test_event_group_and_private_message_early_return(monkeypatch):
    monkeypatch.setattr(main, "unity_enabled", lambda *a, **k: False)
    calls = []
    monkeypatch.setattr(main, "unity_reply", lambda *a: calls.append(a))
    event = SimpleNamespace(bot_info=SimpleNamespace(hash="bot"))
    main.Event.group_message(event, None)
    main.Event.private_message(event, None)
    assert calls == []


def test_event_poke_wiring(monkeypatch):
    monkeypatch.setattr(main, "unity_enabled", lambda *a, **k: True)
    calls = []

    class FakeMsg:
        def __init__(self):
            self.group_id = None
            self.flags = {}

    monkeypatch.setattr(main, "MsgEvent", lambda event: FakeMsg())
    monkeypatch.setattr(main, "unity_reply", lambda plugin_event, proc, msg_event: calls.append(msg_event))
    event = SimpleNamespace(
        bot_info=SimpleNamespace(hash="bot"),
        data=SimpleNamespace(group_id="g1", message="", sender={}, extend={}),
    )
    main.Event.poke(event, None)
    assert len(calls) == 1
    assert calls[0].group_id == "g1"
    assert calls[0].flags["is_group"] is True


def test_event_menu_namespace_mismatch(monkeypatch):
    calls = []
    monkeypatch.setattr(main.OlivaDiceCore.console, "setConsoleSwitchByHash", lambda *a: calls.append(a))
    event = SimpleNamespace(data=SimpleNamespace(namespace="Other", event="MammonRoulette_Menu_main_enabled"))
    main.Event.menu(event, FakeProc())
    assert calls == []


def test_event_menu_manage(monkeypatch):
    monkeypatch.setattr(main, "has_NativeGUI", True)
    monkeypatch.setattr(main, "is_windows", True)

    class FakeConfigUI:
        started = []

        def __init__(self, Model_name=None, logger_proc=None):
            self.Model_name = Model_name

        def start(self):
            FakeConfigUI.started.append(self.Model_name)

    monkeypatch.setattr(MammonRoulette.GUI, "ConfigUI", FakeConfigUI)
    proc = SimpleNamespace(Proc_info=SimpleNamespace(logger_proc=SimpleNamespace(log=lambda msg: None)))
    event = SimpleNamespace(data=SimpleNamespace(namespace="MammonRoulette", event="MammonRoulette_Menu_manage"))
    main.Event.menu(event, proc)
    assert FakeConfigUI.started == ["MammonRoulette_manage"]
