# -*- encoding: utf-8 -*-
"""Defs/effect.py 的效果单元测试。"""

from MammonRoulette.Core.registry import effectReg
from MammonRoulette.Core.work import GameWork

from fakes import add_player, build_game, msg_event_for


def work_for(players, shooter="u1", hp=4):
    game = build_game("经典")
    for user_id in players:
        add_player(game, user_id, hp=hp)
    game["data"]["shooter"] = shooter
    msg_event = msg_event_for(game)
    return game, msg_event, GameWork.from_manager(msg_event)


def test_bind_apply():
    game, msg_event, _work = work_for(["u1", "u2"])
    assert effectReg.get("束缚").apply(msg_event, "u2", 1) is True
    assert game["data"]["players"]["u2"]["effects_event"]["束缚"]["stacks"] == 1


def test_bind_on_moment():
    _game, msg_event, _work = work_for(["u1", "u2"], shooter="u1")
    effect_data = {"stacks": 1, "expired": False}
    effectReg.get("束缚").on_moment(msg_event, "shoot", "u1", effect_data)
    assert effect_data["expired"] is False
    effectReg.get("束缚").on_moment(msg_event, "switch", "u1", effect_data)
    assert effect_data["expired"] is True


def test_neural_pain_apply_new_on_other():
    game, msg_event, work = work_for(["u1", "u2"], shooter="u1")
    work.tmp["source"] = "u1"
    effectReg.get("神经麻痹").apply(msg_event, "u2", 2)
    effect_data = game["data"]["players"]["u2"]["effects_event"]["神经麻痹"]
    assert effect_data["stacks"] == 2
    assert effect_data["settle_due"] is True
    assert effect_data["data"] == [{"dmg": 2, "source": "u1"}]


def test_neural_pain_absorb_damage():
    game, msg_event, work = work_for(["u1", "u2"], shooter="u1")
    effectReg.get("神经麻痹").apply(msg_event, "u2", 0)
    effect_data = game["data"]["players"]["u2"]["effects_event"]["神经麻痹"]
    work.tmp.update({"target": "u2", "dmg": 3, "dmg_type": "", "source": "u1"})
    effectReg.get("神经麻痹").on_moment(msg_event, "damage", "u2", effect_data)
    assert work.tmp["dmg"] == 0
    assert effect_data["stacks"] == 3


def test_neural_pain_settle_on_done(monkeypatch):
    game, msg_event, work = work_for(["u1", "u2"], shooter="u1", hp=4)
    work.tmp["source"] = "u2"
    effectReg.get("神经麻痹").apply(msg_event, "u1", 1)
    effect_data = game["data"]["players"]["u1"]["effects_event"]["神经麻痹"]
    effect_data["settle_due"] = True
    effectReg.get("神经麻痹").on_moment(msg_event, "done", "u1", effect_data)
    assert game["data"]["players"]["u1"]["hp"] == 3
    assert effect_data["expired"] is True


def test_neural_pain_first_done_defers_settle():
    game, msg_event, work = work_for(["u1", "u2"], shooter="u1", hp=4)
    work.tmp["source"] = "u2"
    effectReg.get("神经麻痹").apply(msg_event, "u1", 1)
    effect_data = game["data"]["players"]["u1"]["effects_event"]["神经麻痹"]
    effectReg.get("神经麻痹").on_moment(msg_event, "done", "u1", effect_data)
    assert effect_data["settle_due"] is True
    assert game["data"]["players"]["u1"]["hp"] == 4


def test_neural_pain_settle_without_stacks():
    game, msg_event, work = work_for(["u1", "u2"], shooter="u1", hp=4)
    work.tmp["source"] = "u2"
    effectReg.get("神经麻痹").apply(msg_event, "u1", 0)
    effect_data = game["data"]["players"]["u1"]["effects_event"]["神经麻痹"]
    effect_data["settle_due"] = True
    effectReg.get("神经麻痹").on_moment(msg_event, "done", "u1", effect_data)
    assert effect_data["expired"] is True
