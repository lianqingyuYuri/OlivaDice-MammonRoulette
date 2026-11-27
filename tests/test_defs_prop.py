# -*- encoding: utf-8 -*-
"""Defs/prop.py 的道具单元测试。"""

import random

from MammonRoulette.Core.registry import command, effectReg, propReg
from MammonRoulette.Core.work import GameWork

from fakes import FakePluginEvent, RandSeq, add_player, build_game, msg_event_for


def prop_work(mode="经典", players=("u1", "u2"), shooter="u1", hp=4, props=None, ammo_live=2, ammo_blank=2, bullet=False):
    game = build_game(mode)
    for uid in players:
        add_player(game, uid, hp=hp)
    if props is not None:
        game["data"]["players"][shooter]["props"] = list(props)
    game["data"].update(
        {
            "ammo_live": ammo_live,
            "ammo_blank": ammo_blank,
            "bullet": bullet,
            "shooter": shooter,
        }
    )
    game["data"]["players"][shooter]["actions"] = 1
    msg_event = msg_event_for(game)
    return game, msg_event, GameWork.from_manager(msg_event)


def patch_choice(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])


def test_handcuffs_redirects_and_applies_bind():
    game, msg_event, _work = prop_work(props=["手铐"])
    assert propReg.get("手铐").apply(msg_event, "u1") is True
    assert "束缚" in game["data"]["players"]["u2"]["effects_event"]
    assert game["data"]["players"]["u2"]["actions"] == -1


def test_handcuffs_fails_when_bound():
    game, msg_event, _work = prop_work(props=["手铐"])
    game["data"]["players"]["u2"]["effects_event"]["束缚"] = {"stacks": 1}
    assert propReg.get("手铐").apply(msg_event, "u1") is False


def test_saw_apply_and_moment():
    _game, msg_event, work = prop_work(props=["锯子"])
    assert propReg.get("锯子").apply(msg_event, "u1") is True
    assert propReg.get("锯子").apply(msg_event, "u1") is False
    work.tmp["dmg"] = 1
    prop_data = work.get_prop_data(prop_name="锯子")[0]
    propReg.get("锯子").on_moment(msg_event, "shoot", prop_data)
    assert work.tmp["dmg"] == 2
    assert prop_data["expired"] is True


def test_invite_self_and_other(monkeypatch):
    patch_choice(monkeypatch)
    game, msg_event, _work = prop_work(props=["邀请函"])
    assert propReg.get("邀请函").apply(msg_event, "u1") is True
    assert len(game["data"]["players"]["u1"]["props"]) >= 3
    assert game["data"]["shooter"] == "u2"

    game, msg_event, _work = prop_work(props=["邀请函"])
    assert propReg.get("邀请函").apply(msg_event, "u2") is True
    assert len(game["data"]["players"]["u2"]["props"]) >= 3
    assert game["data"]["shooter"] == "u2"


def test_peanut_and_chocolate_and_smoke(monkeypatch):
    patch_choice(monkeypatch)
    game, msg_event, _work = prop_work(props=["花生", "巧克力", "香烟"], ammo_live=2, ammo_blank=2)
    propReg.get("花生").apply(msg_event, "u1")
    assert game["data"]["ammo_blank"] == 3
    propReg.get("巧克力").apply(msg_event, "u1")
    assert game["data"]["ammo_live"] == 3

    game["data"]["ammo_blank"] = 2
    propReg.get("香烟").apply(msg_event, "u1")
    assert game["data"]["ammo_blank"] == 1
    game["data"]["ammo_blank"] = 0
    game["data"]["ammo_live"] = 2
    propReg.get("香烟").apply(msg_event, "u1")
    assert game["data"]["ammo_live"] == 1


def test_red_cow_heals_self_and_other():
    game, msg_event, _work = prop_work(props=["红牛"])
    propReg.get("红牛").apply(msg_event, "u1")
    assert game["data"]["players"]["u1"]["hp"] == 5
    propReg.get("红牛").apply(msg_event, "u2")
    assert game["data"]["players"]["u2"]["hp"] == 5


def test_magnifier_apply_and_unregister():
    game, msg_event, work = prop_work(props=["放大镜"])
    assert propReg.get("放大镜").apply(msg_event, "u1") is True
    assert game["data"]["modify"]["ammo_visible"] is True
    assert game["data"]["modify"]["bullet_visible"] is True
    assert propReg.get("放大镜").apply(msg_event, "u1") is False

    prop_data = work.get_prop_data(prop_name="放大镜")[0]
    propReg.get("放大镜").on_moment(msg_event, "shoot", prop_data)
    assert prop_data["expired"] is True
    propReg.get("放大镜").on_unregister(msg_event, prop_data)
    assert game["data"]["modify"]["bullet_visible"] is False


def test_lipstick_self_and_other(monkeypatch):
    patch_choice(monkeypatch)
    game, msg_event, _work = prop_work(props=["口红"])
    game["data"]["players"]["u2"]["props"] = ["锯子"]
    propReg.get("口红").apply(msg_event, "u1")
    assert "口红" not in game["data"]["players"]["u1"]["props"]

    game, msg_event, _work = prop_work(props=["口红"])
    game["data"]["players"]["u2"]["props"] = ["锯子"]
    propReg.get("口红").apply(msg_event, "u2")
    assert "锯子" not in game["data"]["players"]["u2"]["props"]
    assert "锯子" in game["data"]["players"]["u1"]["props"]


def test_poker_flips_bullet(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([54]))
    game, msg_event, _work = prop_work(props=["扑克"], ammo_live=2, ammo_blank=2, bullet=True)
    assert propReg.get("扑克").apply(msg_event, "u1") is True
    assert game["data"]["bullet"] is False
    assert game["data"]["ammo_blank"] == 3
    assert game["data"]["ammo_live"] == 1
    assert game["data"]["modify"]["ammo_visible"] is False
    assert game["data"]["modify"]["bullet_visible"] is False


def test_roulette_reloads_and_clears_poker(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([2, 1, 2]))
    game, msg_event, work = prop_work(props=["转盘", "扑克"], ammo_live=2, ammo_blank=2)
    work.register_prop_event({"name": "扑克"})
    assert propReg.get("转盘").apply(msg_event, "u1") is True
    assert game["data"]["ammo_live"] == 1
    assert game["data"]["ammo_blank"] == 1
    assert work.get_prop_data(prop_name="扑克") == []


def test_milk_draws_for_everyone(monkeypatch):
    patch_choice(monkeypatch)
    game, msg_event, _work = prop_work(props=["牛奶"])
    assert propReg.get("牛奶").apply(msg_event, "u1") is True
    assert len(game["data"]["players"]["u1"]["props"]) >= 3
    assert len(game["data"]["players"]["u2"]["props"]) >= 1


def test_pain_killer_self_and_failure():
    game, msg_event, _work = prop_work(props=["止疼药"])
    assert propReg.get("止疼药").apply(msg_event, "u1") is True
    assert "神经麻痹" in game["data"]["players"]["u1"]["effects_event"]
    assert propReg.get("止疼药").apply(msg_event, "u1") is False


def test_firework_without_damage(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([2, 2]))
    game, msg_event, work = prop_work(props=["烟花"])
    assert propReg.get("烟花").apply(msg_event, "u1") is True
    assert work.get_prop_data(prop_name="烟花") == []
    assert len(game["data"]["players"]["u1"]["props"]) >= 1
    assert len(game["data"]["players"]["u2"]["props"]) >= 1


def test_boom_kills_winners(roulette_db, monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1, 1]))
    game, msg_event, _work = prop_work(props=["和你爆了"], hp=4)
    propReg.get("和你爆了").apply(msg_event, "u1")
    assert game["over"] is True


def test_gold_purchase_direct_use(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([2]))
    game, msg_event, work = prop_work(props=["金币"])
    msg_event.val["state"] = "play"
    msg_event.msg = "购买锯子"
    handler, groups = command.search(msg_event)
    assert handler is not None
    plugin_event = FakePluginEvent()
    handler(plugin_event, None, msg_event, groups)
    assert plugin_event.replies
    assert "金币" not in game["data"]["players"]["u1"]["props"]
    assert work.get_prop_data(prop_name="锯子")


def test_gold_purchase_banned_prop():
    _game, msg_event, _work = prop_work(mode="大富翁", props=["金币"])
    msg_event.val["state"] = "play"
    msg_event.msg = "购买手铐"
    handler, groups = command.search(msg_event)
    assert handler is not None
    plugin_event = FakePluginEvent()
    handler(plugin_event, None, msg_event, groups)
    assert any("禁售" in reply for reply in plugin_event.replies)


def test_handcuffs_direct_target():
    game, msg_event, _work = prop_work(props=["手铐"])
    assert propReg.get("手铐").apply(msg_event, "u2") is True
    assert "束缚" in game["data"]["players"]["u2"]["effects_event"]
    assert game["data"]["players"]["u2"]["actions"] == -1


def test_saw_on_moment_non_shoot():
    _game, msg_event, work = prop_work()
    work.tmp["dmg"] = 1
    prop_data = {"name": "锯子", "expired": False}
    propReg.get("锯子").on_moment(msg_event, "reload", prop_data)
    assert work.tmp["dmg"] == 1
    assert prop_data["expired"] is False


def test_magnifier_on_moment_non_shoot():
    _game, msg_event, _work = prop_work()
    prop_data = {"name": "放大镜", "expired": False}
    propReg.get("放大镜").on_moment(msg_event, "reload", prop_data)
    assert prop_data["expired"] is False


def test_poker_joker_existing_and_reload(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([1]))
    game, msg_event, work = prop_work(props=["扑克"], ammo_live=1, ammo_blank=1, bullet=False)
    work.register_prop_event({"name": "扑克"})
    before = len(work.get_prop_data(prop_name="扑克"))
    assert propReg.get("扑克").apply(msg_event, "u1") is True
    assert game["data"]["ammo_blank"] == 0
    assert game["data"]["ammo_live"] == 2
    assert len(work.get_prop_data(prop_name="扑克")) == before
    prop_data = work.get_prop_data(prop_name="扑克")[0]
    propReg.get("扑克").on_moment(msg_event, "reload", prop_data)
    assert prop_data["expired"] is True


def test_roulette_without_poker(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([2, 1, 2]))
    _game, msg_event, work = prop_work(props=["转盘"], ammo_live=2, ammo_blank=2)
    assert propReg.get("转盘").apply(msg_event, "u1") is True
    assert work.get_prop_data(prop_name="扑克") == []


def test_milk_other_target(monkeypatch):
    patch_choice(monkeypatch)
    game, msg_event, _work = prop_work(props=["牛奶"])
    assert propReg.get("牛奶").apply(msg_event, "u2") is True
    assert len(game["data"]["players"]["u2"]["props"]) >= 2
    assert len(game["data"]["players"]["u1"]["props"]) >= 1


def test_gold_purchase_not_shooter():
    _game, msg_event, _work = prop_work(props=["金币"])
    msg_event.val["state"] = "play"
    msg_event.msg = "购买锯子"
    msg_event.user_id = "u2"
    handler, groups = command.search(msg_event)
    plugin_event = FakePluginEvent()
    handler(plugin_event, None, msg_event, groups)
    assert plugin_event.replies


def test_gold_purchase_no_gold():
    _game, msg_event, _work = prop_work(props=[])
    msg_event.val["state"] = "play"
    msg_event.msg = "购买锯子"
    handler, groups = command.search(msg_event)
    plugin_event = FakePluginEvent()
    handler(plugin_event, None, msg_event, groups)
    assert plugin_event.replies


def test_gold_purchase_non_direct(monkeypatch):
    monkeypatch.setattr(random, "randint", RandSeq([1]))
    game, msg_event, _work = prop_work(props=["金币"])
    msg_event.val["state"] = "play"
    msg_event.msg = "购买手铐"
    handler, groups = command.search(msg_event)
    plugin_event = FakePluginEvent()
    handler(plugin_event, None, msg_event, groups)
    assert "手铐" in game["data"]["players"]["u1"]["props"]
    assert "金币" not in game["data"]["players"]["u1"]["props"]


def test_pain_killer_can_use():
    _game, msg_event, _work = prop_work(props=["止疼药"])
    assert propReg.get("止疼药").can_use(msg_event, "u2") is True
    effectReg.get("神经麻痹").apply(msg_event, "u2", 0)
    assert propReg.get("止疼药").can_use(msg_event, "u2") is False


def test_pain_killer_other_target():
    game, msg_event, _work = prop_work(props=["止疼药"])
    assert propReg.get("止疼药").apply(msg_event, "u2") is True
    assert "神经麻痹" in game["data"]["players"]["u2"]["effects_event"]


def test_firework_with_damage(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([1, 2]))
    game, msg_event, _work = prop_work(props=["烟花"], hp=4)
    propReg.get("烟花").apply(msg_event, "u1")
    assert game["data"]["players"]["u1"]["hp"] == 3
    assert game["data"]["players"]["u2"]["hp"] == 4


def test_firework_when_game_over(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([2, 2]))
    game, msg_event, _work = prop_work(props=["烟花"])
    game["over"] = True
    propReg.get("烟花").apply(msg_event, "u1")
    assert game["data"]["players"]["u1"]["props"] == ["烟花"]


def test_firework_on_moment():
    _game, msg_event, work = prop_work(props=["烟花"])
    prop_data = {"name": "烟花", "data": {"reactivation": 0, "draws": 1}}
    propReg.get("烟花").on_moment(msg_event, "shoot", prop_data)
    assert prop_data["data"]["reactivation"] == 0
    work.register_prop_event(prop_data)
    propReg.get("烟花").on_moment(msg_event, "dead", prop_data)
    assert prop_data["data"]["reactivation"] == 1
    assert prop_data["data"]["draws"] == 2


def test_firework_explosion(monkeypatch):
    patch_choice(monkeypatch)
    monkeypatch.setattr(random, "randint", RandSeq([2]))
    game, msg_event, work = prop_work(props=["烟花"], hp=4)
    work.register_prop_event({"name": "烟花", "data": {"reactivation": 1, "draws": 1}})
    propReg.get("烟花").explosion(msg_event, ["u1", "u2"])
    assert game["data"]["players"]["u1"]["hp"] == 3
    assert game["data"]["players"]["u2"]["hp"] == 3
