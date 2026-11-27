# -*- encoding: utf-8 -*-
"""Core/work.py 的 GameWork 单元测试。"""

import random

import MammonRoulette as MR
from AmorLib import DataBase
from MammonRoulette.Core.base import Moment
from MammonRoulette.Core.work import GameWork

from fakes import add_player, build_game, msg_event_for


class RandSeq:
    """按队列返回确定性的随机数。"""

    def __init__(self, values, default=1):
        self.values = list(values)
        self.default = default

    def __call__(self, a, b):
        value = self.values.pop(0) if self.values else self.default
        return min(max(value, a), b)


def make_work(game, msg_event):
    return GameWork.from_manager(msg_event)


def test_game_work_mirror_properties():
    game = build_game("经典")
    game["data"].update(
        {
            "ammo_live": 2,
            "ammo_blank": 3,
            "bullet": True,
            "shooter": "u1",
        }
    )
    game["data"]["modify"].update({"dmg": 2, "ammo_visible": True, "bullet_visible": False})
    add_player(game, "u1", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    assert work.ammo_live == 2
    assert work.ammo_blank == 3
    assert work.ammo_total == 5
    assert work.bullet is True
    assert work.dmg == 2
    assert work.ammo_visible is True
    assert work.bullet_visible is False
    assert work.shooter == "u1"
    assert work.flag_bot is False
    assert work.flag_over is False

    work.ammo_live = 4
    assert game["data"]["ammo_live"] == 4


def test_get_name_and_get_target():
    game = build_game("经典")
    add_player(game, "u1", name="甲", hp=4)
    add_player(game, "u2", name="乙", hp=4)
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    assert work.get_name() == "甲"
    assert work.get_name("u2") == "乙"
    assert work.get_target() == "u2"
    assert work.get_target("2") == "u2"
    assert work.get_target("u2") == "u2"
    assert work.get_target("9") is None


def test_get_state_builds_player_views():
    game = build_game("经典")
    add_player(game, "u1", name="甲", hp=4, actions=1)
    add_player(game, "u2", name="乙", hp=2, actions=0)
    game["data"]["order"] = ["u1"]
    game["data"]["shooter"] = "u1"
    game["data"]["ammo_live"] = 1
    game["data"]["ammo_blank"] = 1
    game["data"]["bullet"] = True
    game["data"]["players"]["u1"]["props"] = ["锯子"]
    game["data"]["players"]["u1"]["effects_event"] = {"束缚": {"stacks": 1}}
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    state = work.get_state()
    assert state.mode_name == "经典"
    assert state.shooter == "u1"
    assert state.alive_count == 1
    assert state.ammo_live == 1
    assert state.pl_self.id == "u1"
    assert state.players[0].is_shooter is True
    assert state.players[1].is_dead is True
    assert isinstance(state.to_vector(), tuple)


def test_upsert_info_and_format_reply(monkeypatch):
    game = build_game("经典")
    add_player(game, "u1", name="甲", hp=4)
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    first_id = work.upsert_info("第一条")
    assert first_id == 1
    work.upsert_info("更新", first_id)
    assert work.reply["info"] == [{"id": 1, "data": "更新"}]

    game["data"]["bullet"] = True
    game["data"]["modify"]["ammo_visible"] = True
    work.reply["below"]["show_ammo"] = True
    work.reply["below"]["show_shooter"] = True
    monkeypatch.setattr(work.msg_event, "msg_format", lambda *a, **k: "OK")
    reply = work.format_reply()
    assert "OK" in reply
    assert work.reply["info"] == []

    work.reply["override"] = "覆盖"
    assert work.format_reply() == "覆盖"


def test_get_and_remove_prop(monkeypatch):
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["data"]["shooter"] = "u1"
    game["data"]["players"]["u1"]["props"] = []
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    assert work.get_prop("u1", "锯子") == "锯子"
    assert work.remove_prop("u1", "锯子") is True
    assert work.remove_prop("u1", "锯子") is False

    work.props_limit = 1
    work.get_prop("u1", "锯子")
    assert work.get_prop("u1", "锯子") is None


def test_register_and_unregister_events():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    work.register_prop_event({"name": "锯子"})
    assert work.get_prop_data(prop_name="锯子")[0]["expired"] is False
    work.register_effect_event("u1", "束缚", {"stacks": 1})
    assert work.get_effect_data("u1", "束缚")["stacks"] == 1
    work.unregister_effect_event("束缚", "u1", 0)
    assert work.get_effect_data("u1", "束缚") is None


def test_join_human_and_bot(roulette_db):
    with DataBase(roulette_db) as db:
        db.insert("gambler", {"user_id": "u1", "name": "甲", "points": 0, "kills": 0, "suicide": 0, "surrender": 0, "wins": 0, "losses": 0})

    game = build_game("经典")
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.join("u1")
    assert game["data"]["players"]["u1"]["name"] == "甲"

    bot_game = build_game("经典")
    bot_event = msg_event_for(bot_game)
    bot_work = make_work(bot_game, bot_event)
    bot_work.join("bot_1", bot_model="达尔文")
    assert bot_game["data"]["players"]["bot_1"]["bot_model"] == "达尔文"
    assert bot_game["data"]["players"]["bot_1"]["name"].startswith("达尔文")


def test_start_human_game(monkeypatch):
    game = build_game("经典", seats=2)
    add_player(game, "u1", hp=4)
    add_player(game, "u2", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    plugin_event = type("PluginEvent", (), {"reply": lambda self, msg: None})()

    monkeypatch.setattr(random, "randint", RandSeq([1, 1, 1]))
    monkeypatch.setattr(random, "shuffle", lambda seq: None)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    work.start(plugin_event)

    assert game["start"] is True
    assert game["data"]["shooter"] in ("u1", "u2")
    assert game["data"]["players"][game["data"]["shooter"]]["actions"] == 1
    assert game["reply"]["info"] == []


def test_shoot_live_and_switch(monkeypatch):
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 2, "ammo_blank": 2, "bullet": True, "shooter": "u1"})
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    monkeypatch.setattr(random, "randint", RandSeq([3]))
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    work.shoot("u2")

    assert game["data"]["ammo_live"] == 1
    assert game["data"]["players"]["u2"]["hp"] == 3
    assert game["data"]["shooter"] == "u2"
    assert game["data"]["players"]["u1"]["actions"] == 0
    assert game["data"]["players"]["u2"]["actions"] == 1


def test_shoot_blank_self_keeps_action(monkeypatch):
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 1, "ammo_blank": 2, "bullet": False, "shooter": "u1"})
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    monkeypatch.setattr(random, "randint", RandSeq([1]))
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    work.shoot("u1")

    assert game["data"]["ammo_blank"] == 1
    assert game["data"]["shooter"] == "u1"
    assert game["data"]["players"]["u1"]["actions"] == 1


def test_damage_kill_and_over(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=1, actions=0)
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    work.damage("u2", 1, "u1")

    assert game["data"]["players"]["u2"]["hp"] == 0
    assert game["data"]["players"]["u1"]["kills"] == 1
    assert game["data"]["order"] == ["u1"]
    assert game["over"] is True


def test_damage_suicide_switch_and_over(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=1, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)

    work.damage("u1", 1, "u1")

    assert game["data"]["players"]["u1"]["suicide"] is True
    assert game["data"]["shooter"] == "u2"
    assert game["data"]["order"] == ["u2"]
    assert game["over"] is True


def test_upsert_info_append_when_id_missing():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.reply["info"] = [{"id": 1, "data": "a"}]
    work.upsert_info("new", 99)
    assert {"id": 99, "data": "new"} in work.reply["info"]


def test_get_prop_data_by_id():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.props_event = [{"id": 5, "name": "锯子"}]
    assert work.get_prop_data(prop_id=5) == [{"id": 5, "name": "锯子"}]
    assert work.get_prop_data(prop_id=9) == []


def test_unregister_prop_event_no_args():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.unregister_prop_event()


def test_draw_prop_break_when_full(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["data"]["players"]["u1"]["props"] = []
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.props_limit = 1
    work.draw_prop("u1", 2)
    assert len(game["data"]["players"]["u1"]["props"]) == 1


def test_start_with_bot(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1, 1, 1]))
    monkeypatch.setattr(random, "shuffle", lambda seq: None)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典", seats=2)
    add_player(game, "bot_1", hp=4, bot_model="达尔文")
    add_player(game, "u2", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    calls = []
    monkeypatch.setattr(MR.Core.registry.botReg, "action", lambda msg_event: calls.append(msg_event))
    plugin_event = type("PluginEvent", (), {"reply": lambda self, msg: None})()
    work.start(plugin_event)
    assert calls
    assert game["start"] is True


def test_reload_and_dead_early_return_when_over(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    game["over"] = True
    assert work.reload() == (0, 0)
    work.dead("u1", "u1")


def test_dead_with_none_source(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.dead("u2", None)
    assert game["data"]["players"]["u1"]["kills"] == 1
    assert game["over"] is True


def test_shoot_with_preset_consume_action(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([3]))
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 2, "ammo_blank": 2, "bullet": True, "shooter": "u1"})
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.tmp["consume_action"] = 0
    work.shoot("u2")
    assert game["data"]["shooter"] == "u1"
    assert game["data"]["players"]["u1"]["actions"] == 1


def test_try_over_when_already_over_and_tied(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    game["over"] = True
    assert work.try_over() is True

    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["data"]["order"] = []
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.try_over()
    assert game["over"] is True


def test_handle_event_unregisters_expired_effect():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["data"]["players"]["u1"]["effects_event"]["束缚"] = {"stacks": 1, "expired": True}
    msg_event = msg_event_for(game)
    work = make_work(game, msg_event)
    work.handle_event(Moment.DONE)
    assert "束缚" not in game["data"]["players"]["u1"]["effects_event"]
