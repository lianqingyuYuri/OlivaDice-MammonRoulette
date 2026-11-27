# -*- encoding: utf-8 -*-
"""msgReply.py 指令处理器的单元测试。"""

import random
import time

from AmorLib import DataBase
from MammonRoulette import msgReply

from fakes import FakeMsgEvent, FakePluginEvent, RandSeq, add_player, build_game


def make_msg_event(game=None, user_id="u1", msg="", state="ob"):
    val = {"game": game if game is not None else {}, "state": state}
    return FakeMsgEvent(val=val, user_id=user_id, msg=msg)


def insert_gambler(db_path, user_id="u1", name="甲", points=10, wins=1, losses=1):
    with DataBase(db_path) as db:
        db.insert(
            "gambler",
            {
                "user_id": user_id,
                "name": name,
                "points": points,
                "kills": 0,
                "suicide": 0,
                "surrender": 0,
                "wins": wins,
                "losses": losses,
            },
        )


def test_signed_inserts_then_updates(roulette_db):
    msg_event = make_msg_event()
    plugin_event = FakePluginEvent()
    msgReply.signed(plugin_event, None, msg_event, ("赌徒甲",))
    with DataBase(roulette_db) as db:
        row = db.select("gambler", "*", "user_id = ?", "u1")[0]
        assert row["name"] == "赌徒甲"
        assert row["points"] == 0

    msgReply.signed(plugin_event, None, msg_event, ("赌徒乙",))
    with DataBase(roulette_db) as db:
        assert db.select("gambler", "name", "user_id = ?", "u1")[0][0] == "赌徒乙"
    assert plugin_event.replies


def test_card_existing_and_missing(roulette_db):
    insert_gambler(roulette_db)
    plugin_event = FakePluginEvent()
    msgReply.card(plugin_event, None, make_msg_event(user_id="u1"), ("",))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.card(plugin_event, None, make_msg_event(user_id="u9"), ("u9",))
    assert plugin_event.replies


def test_leaderboard_returns_rows(roulette_db):
    insert_gambler(roulette_db, user_id="u1", name="甲", points=10)
    insert_gambler(roulette_db, user_id="u2", name="乙", points=20)
    plugin_event = FakePluginEvent()
    msgReply.leaderboard(plugin_event, None, make_msg_event(), ("赏金", "1"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.leaderboard(plugin_event, None, make_msg_event(), ("杀戮", "1"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.leaderboard(plugin_event, None, make_msg_event(), ("自杀", "1"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.leaderboard(plugin_event, None, make_msg_event(), ("投降", "1"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.leaderboard(plugin_event, None, make_msg_event(), ("", "1"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.leaderboard(plugin_event, None, make_msg_event(), ("赏金", "99"))
    assert not plugin_event.replies


def test_match_game_skips_auto_register_when_registered(roulette_db, monkeypatch):
    insert_gambler(roulette_db, user_id="u1")
    calls = []
    monkeypatch.setattr(msgReply, "signed", lambda *args, **kwargs: calls.append(args))
    game = {}
    msgReply.match_game(FakePluginEvent(), None, make_msg_event(game=game, user_id="u1"), ("经典", ""))
    assert calls == []
    assert game["data"]["order"] == ["u1"]


def test_match_game_expired_started(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["start"] = True
    game["expireTime"] = 0
    plugin_event = FakePluginEvent()
    msgReply.match_game(plugin_event, None, make_msg_event(game=game, user_id="u1"), ("经典", ""))
    assert plugin_event.replies
    assert game["start"] is False
    assert game["data"]["order"] == ["u1"]


def test_match_game_started_and_mode_mismatch(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["start"] = True
    game["expireTime"] = 2_000_000_000
    plugin_event = FakePluginEvent()
    msgReply.match_game(plugin_event, None, make_msg_event(game=game, user_id="u2"), ("经典", ""))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.match_game(plugin_event, None, make_msg_event(game=game, user_id="u2"), ("道具", ""))
    assert plugin_event.replies


def test_match_game_user_already_in_order(roulette_db):
    game = build_game("经典", seats=3)
    add_player(game, "u1", hp=4)
    game["expireTime"] = 2_000_000_000
    plugin_event = FakePluginEvent()
    msgReply.match_game(plugin_event, None, make_msg_event(game=game, user_id="u1"), ("经典", ""))
    assert game["data"]["order"] == ["u1"]


def test_match_game_mode_mismatch_prep(roulette_db):
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["expireTime"] = 2_000_000_000
    plugin_event = FakePluginEvent()
    msgReply.match_game(plugin_event, None, make_msg_event(game=game, user_id="u2"), ("道具", ""))
    assert plugin_event.replies


def test_join_bot_full(roulette_db, monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1, 1, 1]))
    monkeypatch.setattr(random, "shuffle", lambda seq: None)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典", seats=2)
    add_player(game, "u1", hp=4)
    plugin_event = FakePluginEvent()
    msgReply.join_bot(plugin_event, None, make_msg_event(game=game, user_id="u1", state="prep"), ("达尔文",))
    assert game["start"] is True


def test_join_bot_returns_when_started():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["start"] = True
    plugin_event = FakePluginEvent()
    msgReply.join_bot(plugin_event, None, make_msg_event(game=game, user_id="u1", state="prep"), ("达尔文",))
    assert not plugin_event.replies


def test_join_game_returns_when_started():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["start"] = True
    plugin_event = FakePluginEvent()
    msgReply.join_game(plugin_event, None, make_msg_event(game=game, user_id="u2", state="ob"), ())
    assert not plugin_event.replies


def test_match_game_builds_and_starts(roulette_db, monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1, 1, 1]))
    monkeypatch.setattr(random, "shuffle", lambda seq: None)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    game = {}
    first = FakePluginEvent()
    msgReply.match_game(first, None, make_msg_event(game=game, user_id="u1"), ("经典", ""))
    assert game["start"] is False
    assert game["data"]["order"] == ["u1"]

    second = FakePluginEvent()
    msgReply.match_game(second, None, make_msg_event(game=game, user_id="u2"), ("经典", ""))
    assert game["start"] is True
    assert game["data"]["order"] == ["u1", "u2"]
    assert second.replies


def test_match_game_seats_error(roulette_db):
    game = {}
    plugin_event = FakePluginEvent()
    msgReply.match_game(plugin_event, None, make_msg_event(game=game, user_id="u1"), ("经典", "9"))
    assert plugin_event.replies
    assert not game


def test_join_bot_not_full(roulette_db, monkeypatch):
    game = build_game("经典", seats=3)
    add_player(game, "u1", hp=4)
    msg_event = make_msg_event(game=game, user_id="u1", state="prep")
    plugin_event = FakePluginEvent()
    monkeypatch.setattr(random, "randint", RandSeq([0]))
    msgReply.join_bot(plugin_event, None, msg_event, ("达尔文",))
    assert any(pl["bot_model"] == "达尔文" for pl in game["data"]["players"].values())
    assert plugin_event.replies


def test_join_game_delegates(roulette_db, monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1, 1, 1]))
    monkeypatch.setattr(random, "shuffle", lambda seq: None)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典", seats=2)
    add_player(game, "u1", hp=4)
    plugin_event = FakePluginEvent()
    msgReply.join_game(plugin_event, None, make_msg_event(game=game, user_id="u2", state="ob"), ())
    assert "u2" in game["data"]["order"]


def test_exit_game_remain_and_dismiss():
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    add_player(game, "u2", hp=4)
    plugin_event = FakePluginEvent()
    msgReply.exit_game(plugin_event, None, make_msg_event(game=game, user_id="u1", state="prep"), ())
    assert "u1" not in game["data"]["order"]
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.exit_game(plugin_event, None, make_msg_event(game=game, user_id="u2", state="prep"), ())
    assert game == {}
    assert plugin_event.replies


def test_shoot_not_shooter_and_shoot(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1]))
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 2, "ammo_blank": 2, "bullet": False, "shooter": "u1"})
    game["start"] = True

    plugin_event = FakePluginEvent()
    msgReply.shoot(plugin_event, None, make_msg_event(game=game, user_id="u2", state="play"), ("开", "2"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.shoot(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("开", "2"))
    assert plugin_event.replies
    assert game["data"]["ammo_blank"] == 1


def test_shoot_self_and_invalid_target(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1]))
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 2, "ammo_blank": 2, "bullet": False, "shooter": "u1"})
    game["start"] = True

    plugin_event = FakePluginEvent()
    msgReply.shoot(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("吞", ""))
    assert game["data"]["ammo_blank"] == 1

    plugin_event = FakePluginEvent()
    msgReply.shoot(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("开", "9"))
    assert not plugin_event.replies


def test_use_prop_branches(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 2, "ammo_blank": 2, "bullet": False, "shooter": "u1"})
    game["data"]["players"]["u1"]["props"] = ["锯子"]
    game["start"] = True

    plugin_event = FakePluginEvent()
    msgReply.use_prop(plugin_event, None, make_msg_event(game=game, user_id="u2", state="play"), ("锯子", "2"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.use_prop(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("红牛", "2"))
    assert plugin_event.replies

    plugin_event = FakePluginEvent()
    msgReply.use_prop(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("锯子", "2"))
    assert plugin_event.replies
    assert game["data"]["players"]["u1"]["props"] == []


def test_use_prop_self_and_invalid_target(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 2, "ammo_blank": 2, "bullet": False, "shooter": "u1"})
    game["data"]["players"]["u1"]["props"] = ["锯子"]
    game["start"] = True

    plugin_event = FakePluginEvent()
    msgReply.use_prop(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("锯子", ""))
    assert game["data"]["players"]["u1"]["props"] == []

    game["data"]["players"]["u1"]["props"] = ["红牛"]
    plugin_event = FakePluginEvent()
    msgReply.use_prop(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ("红牛", "9"))
    assert not plugin_event.replies
    assert game["data"]["players"]["u1"]["props"] == ["红牛"]


def test_surrender_ends_game(roulette_db, monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"]["shooter"] = "u1"
    game["start"] = True
    plugin_event = FakePluginEvent()
    msgReply.surrender(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ())
    assert game["over"] is True
    assert plugin_event.replies


def test_situation_requires_started_game():
    game = build_game("经典")
    plugin_event = FakePluginEvent()
    msgReply.situation(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ())
    assert not plugin_event.replies

    game["start"] = True
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["data"]["shooter"] = "u1"
    game["data"]["ammo_live"] = 1
    game["data"]["ammo_blank"] = 1
    msgReply.situation(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ())
    assert plugin_event.replies


def test_situation_renders_props_and_effects():
    game = build_game("经典")
    add_player(game, "u1", hp=4, actions=1)
    add_player(game, "u2", hp=4, actions=0)
    game["start"] = True
    game["data"].update({"shooter": "u1", "ammo_live": 1, "ammo_blank": 1, "bullet": False})
    game["data"]["players"]["u1"]["props"] = ["锯子", "锯子"]
    game["data"]["players"]["u1"]["effects_event"] = {"束缚": {"stacks": 1}}
    plugin_event = FakePluginEvent()
    msgReply.situation(plugin_event, None, make_msg_event(game=game, user_id="u1", state="play"), ())
    assert plugin_event.replies
