# -*- encoding: utf-8 -*-
"""Defs/bot.py 的 BOT 决策单元测试。"""

from MammonRoulette.Core.base import BaseBot, BotAction
from MammonRoulette.Core.registry import BotRegistry, botReg, effectReg
from MammonRoulette.Core.work import GameWork
from MammonRoulette.Defs.bot import prop_can_use

from fakes import add_player, build_game, msg_event_for


def bot_game(props, enemy_hp=4, bullet=1, bullet_visible=True, props_limit=12, with_enemy=True):
    game = build_game("经典")
    add_player(game, "bot_1", name="BOT", hp=4, actions=1, bot_model="达尔文")
    game["data"]["players"]["bot_1"]["props"] = list(props)
    game["data"]["players"]["bot_1"]["bot_model"] = "达尔文"
    if with_enemy:
        add_player(game, "u2", name="敌人", hp=enemy_hp, actions=0)
    game["data"].update(
        {
            "shooter": "bot_1",
            "bullet": bool(bullet),
            "ammo_live": 1,
            "ammo_blank": 1,
        }
    )
    game["data"]["modify"].update({"bullet_visible": bullet_visible, "ammo_visible": True})
    game["mode"]["props"]["limit"] = props_limit
    msg_event = msg_event_for(game)
    return game, msg_event, GameWork.from_manager(msg_event)


def test_prop_can_use():
    _game, msg_event, _work = bot_game(["手铐"], with_enemy=True)
    assert prop_can_use(msg_event, "手铐", None) is True
    effectReg.get("束缚").apply(msg_event, "u2", 1)
    assert prop_can_use(msg_event, "手铐", "u2") is False
def test_decide_uses_handcuffs():
    _game, msg_event, work = bot_game(["手铐"], enemy_hp=2)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "手铐"
    assert action.target == "u2"


def test_decide_uses_red_cow_on_self():
    _game, msg_event, work = bot_game(["红牛"], enemy_hp=2)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "红牛"
    assert action.target == "bot_1"


def test_decide_saw_when_bullet_visible_live():
    _game, msg_event, work = bot_game(["锯子"], enemy_hp=2, bullet=1, bullet_visible=True)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "锯子"


def test_decide_poker_when_bullet_visible_blank():
    _game, msg_event, work = bot_game(["扑克"], enemy_hp=2, bullet=0, bullet_visible=True)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "扑克"
    assert action.memory == {"bullet": 1, "bullet_visible": True}


def test_decide_shoot_self_on_blank_without_props():
    _game, msg_event, work = bot_game([], enemy_hp=2, bullet=0, bullet_visible=True)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "shoot"
    assert action.target == ""


def test_decide_magnifier_when_bullet_hidden():
    _game, msg_event, work = bot_game(["放大镜"], enemy_hp=2, bullet=1, bullet_visible=False)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "放大镜"


def test_decide_shoot_other_by_default():
    _game, msg_event, work = bot_game([], enemy_hp=2, bullet=1, bullet_visible=True, props_limit=0)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "shoot"
    assert action.target == "u2"


def test_decide_lipstick_steals_from_enemy_with_props():
    game, msg_event, work = bot_game(["口红"], enemy_hp=2)
    game["data"]["players"]["u2"]["props"] = ["锯子"]
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "口红"
    assert action.target == "u2"


def test_decide_firework():
    _game, msg_event, work = bot_game(["烟花"], enemy_hp=2, bullet=1, bullet_visible=True)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "烟花"
    assert action.target == "bot_1"


def test_decide_chocolate_on_blank():
    _game, msg_event, work = bot_game(["巧克力"], enemy_hp=2, bullet=0, bullet_visible=True)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "巧克力"


def test_decide_invite_when_bullet_hidden():
    _game, msg_event, work = bot_game(["邀请函"], enemy_hp=2, bullet=1, bullet_visible=False, props_limit=12)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "邀请函"


def test_decide_near_full_inventory():
    _game, msg_event, work = bot_game(["巧克力"], enemy_hp=2, bullet=1, bullet_visible=True, props_limit=2)
    action = botReg.get("达尔文").decide(msg_event, work.get_state(), {})
    assert action.type == "use_prop"
    assert action.prop == "巧克力"


def test_bot_action_shoot_other():
    game, msg_event, _work = bot_game([], enemy_hp=4, bullet=1, bullet_visible=True, props_limit=6)
    botReg.action(msg_event)
    assert game["data"]["shooter"] == "u2"
    assert game["data"]["players"]["u2"]["hp"] == 3


def test_bot_action_shoot_self(roulette_db):
    class SelfShooterBot(BaseBot):
        name = "自爆BOT"

        @classmethod
        def decide(cls, msg_event, state, memory):
            return BotAction.shoot()

    registry = BotRegistry()
    registry.botDef()(SelfShooterBot)
    game = build_game("经典")
    add_player(game, "bot_1", hp=1, actions=1, bot_model="自爆BOT")
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 1, "ammo_blank": 1, "bullet": True, "shooter": "bot_1"})
    msg_event = msg_event_for(game)
    registry.action(msg_event)
    assert game["over"] is True


def test_bot_action_use_prop():
    class PropThenShootBot(BaseBot):
        name = "道具BOT"

        @classmethod
        def decide(cls, msg_event, state, memory):
            if memory.get("used"):
                return BotAction.shoot("u2")
            return BotAction.use_prop("锯子", state.pl_self.id, memory={"used": True})

    registry = BotRegistry()
    registry.botDef()(PropThenShootBot)
    game = build_game("经典")
    add_player(game, "bot_1", hp=4, actions=1, bot_model="道具BOT")
    add_player(game, "u2", hp=4, actions=0)
    game["data"]["players"]["bot_1"]["props"] = ["锯子"]
    game["data"].update({"ammo_live": 1, "ammo_blank": 1, "bullet": True, "shooter": "bot_1"})
    msg_event = msg_event_for(game)
    registry.action(msg_event)
    assert game["data"]["shooter"] == "u2"
    assert "锯子" not in game["data"]["players"]["bot_1"]["props"]


def test_bot_action_use_prop_on_other():
    class PropOtherThenShootBot(BaseBot):
        name = "道具BOT2"

        @classmethod
        def decide(cls, msg_event, state, memory):
            if memory.get("used"):
                return BotAction.shoot("u2")
            return BotAction.use_prop("手铐", "u2", memory={"used": True})

    registry = BotRegistry()
    registry.botDef()(PropOtherThenShootBot)
    game = build_game("经典")
    add_player(game, "bot_1", hp=4, actions=1, bot_model="道具BOT2")
    add_player(game, "u2", hp=4, actions=0)
    game["data"]["players"]["bot_1"]["props"] = ["手铐"]
    game["data"].update({"ammo_live": 1, "ammo_blank": 1, "bullet": True, "shooter": "bot_1"})
    msg_event = msg_event_for(game)
    registry.action(msg_event)
    assert game["data"]["shooter"] == "u2"


def test_bot_action_default_shoots_self():
    class DefaultShootBot(BaseBot):
        name = "默认BOT"

        @classmethod
        def decide(cls, msg_event, state, memory):
            return BotAction.shoot()

    registry = BotRegistry()
    registry.botDef()(DefaultShootBot)
    game = build_game("经典")
    add_player(game, "bot_1", hp=4, actions=1, bot_model="默认BOT")
    add_player(game, "u2", hp=4, actions=0)
    game["data"].update({"ammo_live": 1, "ammo_blank": 1, "bullet": True, "shooter": "bot_1"})
    msg_event = msg_event_for(game)
    registry.action(msg_event)
    assert game["data"]["shooter"] == "u2"
    assert game["data"]["players"]["bot_1"]["hp"] == 3
