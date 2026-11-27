# -*- encoding: utf-8 -*-
"""Core/registry.py 的注册器与过滤器单元测试。"""

from MammonRoulette.Core.base import BaseBot, BaseEffect, BaseMode, BaseProp
from AmorLib import HandlerFilter

from MammonRoulette.Core.registry import (
    BotRegistry,
    CommandRegistry,
    EffectRegistry,
    ModeRegistry,
    MsgRegexFilter,
    NameFilter,
    PlStateFilter,
    PropRegistry,
)

from fakes import FakeMsgEvent, add_player, build_game, msg_event_for


def test_pl_state_filter():
    flt = PlStateFilter(("play", "prep"))
    assert flt.filter(FakeMsgEvent(val={"state": "play"})) is True
    assert flt.filter(FakeMsgEvent(val={"state": "ob"})) is False
    assert flt.filter(FakeMsgEvent(val={})) is False


def test_msg_regex_filter():
    flt = MsgRegexFilter("^(吞|开)(.*)$")
    event = FakeMsgEvent(val={}, msg="开枪")
    assert flt.filter(event) is True
    assert flt.match.groups() == ("开", "枪")
    assert MsgRegexFilter("^$").filter(FakeMsgEvent(val={}, msg="x")) is False


def test_name_filter():
    class Named:
        name = "阿尔法"

    assert NameFilter(Named).filter("阿尔法") is True
    assert NameFilter(Named).filter("贝塔") is False


def test_command_registry_search():
    registry = CommandRegistry()

    @registry.plState("play")
    @registry.msgRegex("^(吞|开)枪(\\d*)$")
    def shoot(plugin_event, Proc, msg_event, groups):
        return groups

    event = FakeMsgEvent(val={"state": "play"}, msg="开枪")
    handler, groups = registry.search(event)
    assert handler is shoot
    assert groups == ("开", "")

    assert registry.search(FakeMsgEvent(val={"state": "ob"}, msg="开枪")) == (None, None)


def test_mode_registry_get_fallback_and_trigger():
    registry = ModeRegistry()
    assert registry.get("不存在") is BaseMode
    assert registry.list() == []
    registry.trigger(FakeMsgEvent(val={}), "reload")


def test_mode_registry_mode_def():
    registry = ModeRegistry()
    init_after_called = []

    class DemoMode(BaseMode):
        name = "测试模式"
        points = 7

        class seats(BaseMode.seats):
            default = 3
            max = 5
            min = 2

        class props(BaseMode.props):
            pool = ("锯子",)
            allowed = ()
            banned = ("手铐",)
            limit = 4

        class modify(BaseMode.modify):
            dmg = 2
            ammo_visible = False
            bullet_visible = True

        @classmethod
        def init(cls):
            init_after_called.append("init")

        @classmethod
        def init_after(cls):
            init_after_called.append("init_after")

    registry.modeDef()(DemoMode)
    assert registry.get("测试模式") is DemoMode
    assert registry.list() == ["测试模式"]
    registry.init_after()
    assert init_after_called == ["init", "init_after"]


def test_prop_registry_get_and_apply():
    registry = PropRegistry()
    assert registry.get("不存在") is BaseProp

    class DemoProp(BaseProp):
        name = "测试道具"

        @classmethod
        def apply(cls, msg_event, target):
            return True

    registry.propDef()(DemoProp)
    game = build_game("经典")
    add_player(game, "u1", hp=4)
    game["data"]["order"] = ["u1"]
    game["data"]["players"]["u1"]["props"] = ["测试道具"]
    game["data"]["shooter"] = "u1"
    msg_event = msg_event_for(game, state="play")
    registry.apply(msg_event, "测试道具", "u1", "u1")
    assert "测试道具" not in game["data"]["players"]["u1"]["props"]


def test_effect_registry_get_and_def():
    registry = EffectRegistry()
    assert registry.get("不存在") is BaseEffect

    class DemoEffect(BaseEffect):
        name = "测试效果"

    registry.effectDef()(DemoEffect)
    assert registry.get("测试效果") is DemoEffect
    assert registry.list() == ["测试效果"]


def test_bot_registry_get_and_def():
    registry = BotRegistry()
    assert registry.get("不存在") is BaseBot

    class DemoBot(BaseBot):
        name = "测试BOT"

    registry.botDef()(DemoBot)
    assert registry.get("测试BOT") is DemoBot
    assert registry.list() == ["测试BOT"]


class _AnyFilter(HandlerFilter[str]):
    def filter(self, event):
        return True


def test_registry_get_falls_back_without_name_filter():
    for registry_cls, fallback in (
        (ModeRegistry, BaseMode),
        (PropRegistry, BaseProp),
        (EffectRegistry, BaseEffect),
        (BotRegistry, BaseBot),
    ):
        registry = registry_cls()
        registry.attach("占位", _AnyFilter())
        assert registry.get("占位") is fallback
