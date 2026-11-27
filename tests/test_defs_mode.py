# -*- encoding: utf-8 -*-
"""Defs/mode.py 中各模式钩子的单元测试。"""

import random

import MammonRoulette as MR
from MammonRoulette.Core.work import GameWork
from MammonRoulette.Defs.mode import generate_helpdoc

from fakes import RandSeq, add_player, build_game, msg_event_for


def work_for(mode_name, players, shooter="u1", ammo_live=2, ammo_blank=2, bullet=False):
    """构造指定模式的对局与 GameWork。"""
    game = build_game(mode_name)
    for user_id, hp in players:
        add_player(game, user_id, hp=hp)
    game["data"].update(
        {
            "ammo_live": ammo_live,
            "ammo_blank": ammo_blank,
            "bullet": bullet,
            "shooter": shooter,
        }
    )
    msg_event = msg_event_for(game)
    return game, msg_event, GameWork.from_manager(msg_event)


def test_generate_helpdoc_all_fields():
    text = generate_helpdoc(
        points=50,
        hp_str="每名玩家 4hp.",
        props_limit=6,
        props_pool=("锯子", "花生"),
        props_allowed=("手铐",),
        props_banned=("口红",),
        mechanisms=("机制A", "机制B"),
    )
    assert "〈赏金〉50" in text
    assert "〈血量〉每名玩家 4hp." in text
    assert "〈道具池〉(上限6)" in text
    assert "锯子, 花生" in text
    assert "-特殊道具-" in text
    assert "-禁用道具-" in text
    assert "〔机制〕" in text
    assert "1. 机制A;" in text
    assert "2. 机制B." in text


def test_generate_helpdoc_empty():
    assert generate_helpdoc() == ""


def test_classic_start_join_switch(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, _work = work_for("经典", [("u1", 4), ("u2", 4)], shooter="u1")
    MR.Core.registry.modeReg.get("经典").start(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == 2
    assert len(game["data"]["players"]["u2"]["props"]) == 1

    MR.Core.registry.modeReg.get("经典").join(msg_event, "u1")
    assert game["data"]["players"]["u1"]["hp"] == 4

    MR.Core.registry.modeReg.get("经典").switch(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == 4


def test_item_mode_join_and_reload(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, _work = work_for("道具", [("u1", 4), ("u2", 4), ("u3", 4)], shooter="u1")
    MR.Core.registry.modeReg.get("道具").join(msg_event, "u3")
    assert game["data"]["players"]["u3"]["hp"] == 5
    add_player(game, "u4", hp=4)
    MR.Core.registry.modeReg.get("道具").join(msg_event, "u4")
    assert game["data"]["players"]["u4"]["hp"] == 6

    MR.Core.registry.modeReg.get("道具").reload(msg_event)
    for uid in ("u1", "u2", "u3", "u4"):
        assert len(game["data"]["players"][uid]["props"]) == 4


def test_gold_mode_start_join_switch_damage(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, work = work_for("金币", [("u1", 5), ("u2", 5)], shooter="u1")
    MR.Core.registry.modeReg.get("金币").start(msg_event)
    assert game["data"]["players"]["u1"]["props"] == ["金币"]
    assert game["data"]["players"]["u2"]["props"] == []

    MR.Core.registry.modeReg.get("金币").join(msg_event, "u2")
    assert game["data"]["players"]["u2"]["hp"] == 5

    MR.Core.registry.modeReg.get("金币").switch(msg_event)
    assert game["data"]["players"]["u1"]["props"] == ["金币", "金币"]

    game["data"]["modify"]["dmg"] = 4
    work.tmp["target"] = "u2"
    MR.Core.registry.modeReg.get("金币").damage(msg_event)
    assert "金币" in game["data"]["players"]["u2"]["props"]
    assert game["data"]["modify"]["金币"] == ["u2"]


def test_hero_mode_start_join_shoot(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, work = work_for("勇者", [("u1", 5), ("u2", 5)], shooter="u1")
    MR.Core.registry.modeReg.get("勇者").start(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == 1
    assert len(game["data"]["players"]["u2"]["props"]) == 2

    MR.Core.registry.modeReg.get("勇者").join(msg_event, "u1")
    assert game["data"]["players"]["u1"]["hp"] == 5

    # 实弹 + 魔弹判定命中 => 伤害 +1
    game["data"]["bullet"] = True
    work.tmp.update({"target": "u2", "is_shoot_me": False, "dmg": 1})
    monkeypatch.setattr(random, "randint", RandSeq([1]))
    MR.Core.registry.modeReg.get("勇者").shoot(msg_event)
    assert work.tmp["dmg"] == 2

    # 吞枪且空弹 => 抽 2 张
    game["data"]["bullet"] = False
    work.tmp.update({"target": "u1", "is_shoot_me": True, "dmg": 1})
    before = len(game["data"]["players"]["u1"]["props"])
    monkeypatch.setattr(random, "randint", RandSeq([3]))
    MR.Core.registry.modeReg.get("勇者").shoot(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == before + 2


def test_gambler_mode_start_join_shoot_poker(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, work = work_for("赌徒", [("u1", 5), ("u2", 5)], shooter="u1")
    MR.Core.registry.modeReg.get("赌徒").start(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == 2
    assert len(game["data"]["players"]["u2"]["props"]) == 2

    MR.Core.registry.modeReg.get("赌徒").join(msg_event, "u1")
    assert game["data"]["players"]["u1"]["hp"] == 5

    # 吞枪空弹 => 抽 3 张
    game["data"]["bullet"] = False
    work.tmp.update({"target": "u1", "is_shoot_me": True, "dmg": 1})
    before = len(game["data"]["players"]["u1"]["props"])
    monkeypatch.setattr(random, "randint", RandSeq([3]))
    MR.Core.registry.modeReg.get("赌徒").shoot(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == before + 3

    assert MR.Core.registry.modeReg.get("赌徒").poker()


def test_monopoly_start_join_try_over_damage(monkeypatch, roulette_db):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    MR.Core.registry.modeReg.get("大富翁").start(msg_event)
    assert game["data"]["modify"]["gold"] == 0
    assert game["data"]["modify"]["order_copy"] == ["u1", "u2"]
    assert len(game["data"]["players"]["u1"]["props"]) == 2

    MR.Core.registry.modeReg.get("大富翁").join(msg_event, "u2")
    assert game["data"]["players"]["u2"]["hp"] == 2

    assert MR.Core.registry.modeReg.get("大富翁").try_over(msg_event) is False
    game["data"]["players"]["u1"]["props"] = ["金币"] * 6
    assert MR.Core.registry.modeReg.get("大富翁").try_over(msg_event) is True
    assert work.order == ["u1"]

    work.tmp.update({"is_attack_me": False, "source": "u1", "dmg": 1})
    before = len(game["data"]["players"]["u1"]["props"])
    MR.Core.registry.modeReg.get("大富翁").damage(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == before + 1


def test_monopoly_dead_loan_revives(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([2]))
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    game["data"]["modify"]["order_copy"] = ["u1", "u2"]
    game["data"]["modify"]["gold"] = 0
    game["data"]["players"]["u2"]["props"] = ["金币", "金币", "金币"]
    work.tmp.update({"target": "u2", "source": "u1", "is_attack_me": False})
    MR.Core.registry.modeReg.get("大富翁").dead(msg_event)
    assert game["data"]["players"]["u2"]["hp"] == 2
    assert game["data"]["players"]["u1"]["props"].count("金币") == 2
    assert game["data"]["order"] == ["u1", "u2"]
    assert game["data"]["modify"]["gold"] == 1


def test_monopoly_dead_surrender_removes_from_copy():
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    game["data"]["modify"]["order_copy"] = ["u1", "u2"]
    game["data"]["players"]["u2"]["surrender"] = True
    work.tmp.update({"target": "u2", "source": "u1", "is_attack_me": True})
    MR.Core.registry.modeReg.get("大富翁").dead(msg_event)
    assert "u2" not in game["data"]["modify"]["order_copy"]


def test_gold_damage_skip_when_already_compensated():
    game, msg_event, work = work_for("金币", [("u1", 5), ("u2", 5)], shooter="u1")
    game["data"]["modify"]["dmg"] = 4
    game["data"]["modify"]["金币"] = ["u2"]
    work.tmp["target"] = "u2"
    MR.Core.registry.modeReg.get("金币").damage(msg_event)
    assert game["data"]["modify"]["金币"] == ["u2"]


def test_gold_damage_with_full_inventory(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    game, msg_event, work = work_for("金币", [("u1", 5), ("u2", 5)], shooter="u1")
    game["data"]["modify"]["dmg"] = 4
    game["data"]["players"]["u2"]["props"] = ["占位"] * 12
    work.tmp["target"] = "u2"
    MR.Core.registry.modeReg.get("金币").damage(msg_event)
    assert game["data"]["modify"]["金币"] == ["u2"]
    assert len(game["data"]["players"]["u2"]["props"]) == 12


def test_gambler_poker_returns_suit_and_rank(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([54]))
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    assert MR.Core.registry.modeReg.get("赌徒").poker()


def test_gambler_shoot_poker_flips_bullet(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([1]))
    game, msg_event, work = work_for("赌徒", [("u1", 5), ("u2", 5)], shooter="u1")
    game["data"].update({"ammo_live": 2, "ammo_blank": 1, "bullet": True})
    work.tmp.update({"target": "u2", "is_shoot_me": False, "dmg": 1})
    MR.Core.registry.modeReg.get("赌徒").shoot(msg_event)
    assert game["data"]["bullet"] is False
    assert game["data"]["ammo_live"] == 1
    assert game["data"]["ammo_blank"] == 2


def test_gambler_shoot_magic_bullet(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([3, 1]))
    game, msg_event, work = work_for("赌徒", [("u1", 5), ("u2", 5)], shooter="u1")
    game["data"].update({"ammo_live": 2, "ammo_blank": 1, "bullet": True})
    work.tmp.update({"target": "u2", "is_shoot_me": False, "dmg": 1})
    MR.Core.registry.modeReg.get("赌徒").shoot(msg_event)
    assert work.tmp["dmg"] == 2


def test_gambler_shoot_poker_flips_blank(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([1, 3]))
    game, msg_event, work = work_for("赌徒", [("u1", 5), ("u2", 5)], shooter="u1")
    game["data"].update({"ammo_live": 1, "ammo_blank": 2, "bullet": False})
    work.tmp.update({"target": "u2", "is_shoot_me": False, "dmg": 1})
    MR.Core.registry.modeReg.get("赌徒").shoot(msg_event)
    assert game["data"]["bullet"] is True
    assert game["data"]["ammo_blank"] == 1
    assert game["data"]["ammo_live"] == 2


def test_monopoly_damage_skip_when_self_attack():
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    work.tmp.update({"is_attack_me": True, "source": "u1", "dmg": 1})
    before = len(game["data"]["players"]["u1"]["props"])
    MR.Core.registry.modeReg.get("大富翁").damage(msg_event)
    assert len(game["data"]["players"]["u1"]["props"]) == before


def test_monopoly_dead_no_gold(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([2]))
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    game["data"]["modify"]["order_copy"] = ["u1", "u2"]
    game["data"]["modify"]["gold"] = 0
    work.tmp.update({"target": "u2", "source": "u1", "is_attack_me": False})
    MR.Core.registry.modeReg.get("大富翁").dead(msg_event)
    assert game["data"]["players"]["u2"]["hp"] == 2
    assert game["data"]["order"] == ["u1", "u2"]


def test_monopoly_dead_self_attack_skips_loot(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([2]))
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    game["data"]["modify"]["order_copy"] = ["u1", "u2"]
    game["data"]["modify"]["gold"] = 0
    game["data"]["players"]["u2"]["props"] = ["金币", "金币", "金币"]
    work.tmp.update({"target": "u2", "source": "u1", "is_attack_me": True})
    MR.Core.registry.modeReg.get("大富翁").dead(msg_event)
    assert game["data"]["players"]["u2"]["props"].count("金币") == 1


def test_monopoly_dead_jackpot_win(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", RandSeq([1, 5]))
    game, msg_event, work = work_for("大富翁", [("u1", 2), ("u2", 2)], shooter="u1")
    game["data"]["modify"]["order_copy"] = ["u1", "u2"]
    game["data"]["modify"]["gold"] = 2
    game["data"]["players"]["u2"]["props"] = ["金币"]
    work.tmp.update({"target": "u2", "source": "u1", "is_attack_me": True})
    MR.Core.registry.modeReg.get("大富翁").dead(msg_event)
    assert game["data"]["players"]["u2"]["props"].count("金币") == 2
    assert game["data"]["modify"]["gold"] == 0
