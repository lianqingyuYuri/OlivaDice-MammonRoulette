# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Core/event.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from __future__ import annotations

import re
from typing import Any, Protocol, cast

from AmorLib import STRING_ROW, Entry, HandlerFilter, MsgEvent, Registry

import MammonRoulette as MR


# region 指令注册
class CommandHandler(Protocol):
    __name__: str

    def __call__(self, plugin_event, Proc, msg_event, groups) -> None: ...


class PlStateFilter(HandlerFilter[MsgEvent]):
    """按玩家状态过滤"""

    def __init__(self, states: str | STRING_ROW):
        self.states = set((states,) if isinstance(states, str) else states)

    def filter(self, msg_event: MsgEvent) -> bool:
        state = msg_event.val.get("state")
        return not (state is None or state not in self.states)


class MsgRegexFilter(HandlerFilter[MsgEvent]):
    """按消息正则过滤"""

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)
        self.match = None

    def filter(self, msg_event: MsgEvent) -> bool:
        self.match = self.pattern.search(msg_event.msg)
        return self.match is not None


class CommandRegistry(Registry[MsgEvent]):
    def msgRegex(self, pattern: str, helpdoc: str | None = None):
        def decorator(func):
            if helpdoc is not None:
                doc = MR.custom.dictHelpDocTemplate["default"]
                doc["恶赌 命令"] = helpdoc if not doc.get("恶赌 命令") else f"{doc['恶赌 命令']}\n{helpdoc}"
            self.attach(func, MsgRegexFilter(pattern))
            return func

        return decorator

    def plState(self, states: str | STRING_ROW):
        def decorator(func):
            self.attach(func, PlStateFilter(states))
            return func

        return decorator

    def search(self, msg_event: MsgEvent) -> tuple[CommandHandler | None, tuple | None]:
        for entry in self.match_handlers(msg_event):
            for flt in entry.filters:
                if isinstance(flt, MsgRegexFilter):
                    return cast(CommandHandler, entry.key), flt.match.groups() if flt.match else ()
        return None, None


# endregion


# region 通用注册
class NameFilter(HandlerFilter[str]):
    """按名称匹配注册类，供模式/道具/效果/BOT注册器共用。"""

    def __init__(self, def_cls: Any):
        self.def_cls = def_cls

    def filter(self, name: str) -> bool:
        return name == self.def_cls.name


# endregion


# region 模式注册
class ModeRegistry(Registry[str]):
    """以模式名为键注册模式，模式类挂在过滤器上，运行期按对局模式名派发。"""

    _entries: dict[str, Entry[str]]

    def modeDef(self, helpDocDefault: dict | None = None, strCustomDefault: dict | None = None):
        """注册模式"""
        helpDocDefault = helpDocDefault if helpDocDefault is not None else {}
        strCustomDefault = strCustomDefault if strCustomDefault is not None else {}

        def decorator(mode_cls: type[MR.Core.base.BaseMode]):
            mode_name = mode_cls.name
            MR.custom.dictHelpDocTemplate["default"].update(helpDocDefault)
            for field, (note, msg) in strCustomDefault.items():
                MR.custom.dictStrCustomNote[field] = note
                MR.custom.dictStrCustomTemplate["default"][field] = msg
            mode_cls.init()
            MR.custom.dictModeCustom["default"][mode_name] = {
                "points": mode_cls.points,
                "seats": {
                    "default": mode_cls.seats.default,
                    "max": mode_cls.seats.max,
                    "min": mode_cls.seats.min,
                },
                "props": {
                    "pool": mode_cls.props.pool,
                    "allowed": mode_cls.props.allowed,
                    "banned": mode_cls.props.banned,
                    "limit": mode_cls.props.limit,
                },
                "modify": {
                    "dmg": mode_cls.modify.dmg,
                    "ammo_visible": mode_cls.modify.ammo_visible,
                    "bullet_visible": mode_cls.modify.bullet_visible,
                },
            }
            self.attach(mode_cls.name, NameFilter(mode_cls))
            return mode_cls

        return decorator

    def init_after(self):
        """在所有模式注册完成后调用"""
        for entry in self._entries.values():
            for flt in entry.filters:
                if isinstance(flt, NameFilter):
                    flt.def_cls.init_after()
                    break
        return

    def get(self, name: str) -> type[MR.Core.base.BaseMode]:
        """按模式名取模式类 O(1)"""
        entry = self._entries.get(name)
        if entry is None:
            return MR.Core.base.BaseMode
        for flt in entry.filters:
            if isinstance(flt, NameFilter):
                return flt.def_cls
        return MR.Core.base.BaseMode

    def list(self) -> list[str]:
        return list(self._entries.keys())

    def trigger(self, msg_event: MsgEvent, moment: MR.Core.base.Moment) -> None:
        """按当前对局模式名派发生命周期钩子。"""
        mode_name = msg_event.val.get("game", {}).get("mode", {}).get("name")
        mode_cls = self.get(mode_name) if mode_name is not None else None
        if mode_cls is None:
            return
        getattr(mode_cls, moment)(msg_event)
        return


# endregion


# region 道具注册
class PropRegistry(Registry[str]):
    """以道具名为键注册道具，道具类挂在过滤器上。"""

    _entries: dict[str, Entry[str]]

    def propDef(self, helpDocDefault: dict | None = None, strCustomDefault: dict | None = None):
        """注册道具"""
        helpDocDefault = helpDocDefault if helpDocDefault is not None else {}
        strCustomDefault = strCustomDefault if strCustomDefault is not None else {}

        def decorator(prop_cls: type[MR.Core.base.BaseProp]):
            prop_name = prop_cls.name
            MR.custom.dictHelpDocTemplate["default"].update(helpDocDefault)
            for field, (note, msg) in strCustomDefault.items():
                MR.custom.dictStrCustomNote[field] = note
                MR.custom.dictStrCustomTemplate["default"][field] = msg
            prop_cls.init()
            MR.custom.dictPropCustom["default"][prop_name] = {}
            self.attach(prop_cls.name, NameFilter(prop_cls))
            return prop_cls

        return decorator

    def init_after(self):
        """在所有道具注册完成后调用"""
        for entry in self._entries.values():
            for flt in entry.filters:
                if isinstance(flt, NameFilter):
                    flt.def_cls.init_after()
                    break
        return

    def get(self, name: str) -> type[MR.Core.base.BaseProp]:
        """按道具名取道具类 O(1)"""
        entry = self._entries.get(name)
        if entry is None:
            return MR.Core.base.BaseProp
        for flt in entry.filters:
            if isinstance(flt, NameFilter):
                return flt.def_cls
        return MR.Core.base.BaseProp

    def list(self) -> list[str]:
        return list(self._entries.keys())

    def apply(self, msg_event: MsgEvent, prop_name: str, user_id: str, target: str) -> None:
        """使用道具，使用成功后从使用者手中移除该道具。"""
        prop_cls = self.get(prop_name)
        if prop_cls is not None and prop_cls.apply(msg_event, target):
            MR.Core.work.GameWork.from_manager(msg_event).remove_prop(user_id, prop_name)
        return


# endregion


# region 效果注册
class EffectRegistry(Registry[str]):
    """以效果名为键注册效果，效果类挂在过滤器上。"""

    _entries: dict[str, Entry[str]]

    def effectDef(self, helpDocDefault: dict | None = None, strCustomDefault: dict | None = None):
        """注册效果"""
        helpDocDefault = helpDocDefault if helpDocDefault is not None else {}
        strCustomDefault = strCustomDefault if strCustomDefault is not None else {}

        def decorator(effect_cls: type[MR.Core.base.BaseEffect]):
            effect_name = effect_cls.name
            MR.custom.dictHelpDocTemplate["default"].update(helpDocDefault)
            for field, (note, msg) in strCustomDefault.items():
                MR.custom.dictStrCustomNote[field] = note
                MR.custom.dictStrCustomTemplate["default"][field] = msg
            effect_cls.init()
            MR.custom.dictEffectCustom["default"][effect_name] = {}
            self.attach(effect_cls.name, NameFilter(effect_cls))
            return effect_cls

        return decorator

    def init_after(self):
        """在所有效果注册完成后调用"""
        for entry in self._entries.values():
            for flt in entry.filters:
                if isinstance(flt, NameFilter):
                    flt.def_cls.init_after()
                    break
        return

    def get(self, name: str) -> type[MR.Core.base.BaseEffect]:
        """按效果名取效果类 O(1)"""
        entry = self._entries.get(name)
        if entry is None:
            return MR.Core.base.BaseEffect
        for flt in entry.filters:
            if isinstance(flt, NameFilter):
                return flt.def_cls
        return MR.Core.base.BaseEffect

    def list(self) -> list[str]:
        return list(self._entries.keys())


# endregion


# region BOT注册
class BotRegistry(Registry[str]):
    """以BOT名为键注册BOT，BOT类挂在过滤器上。"""

    _entries: dict[str, Entry[str]]

    def botDef(self):
        """注册BOT"""

        def decorator(bot_cls: type[MR.Core.base.BaseBot]):
            bot_cls.init()
            self.attach(bot_cls.name, NameFilter(bot_cls))
            return bot_cls

        return decorator

    def init_after(self):
        """在所有BOT注册完成后调用"""
        for entry in self._entries.values():
            for flt in entry.filters:
                if isinstance(flt, NameFilter):
                    flt.def_cls.init_after()
                    break
        return

    def get(self, name: str) -> type[MR.Core.base.BaseBot]:
        """按BOT名取BOT类 O(1)"""
        entry = self._entries.get(name)
        if entry is None:
            return MR.Core.base.BaseBot
        for flt in entry.filters:
            if isinstance(flt, NameFilter):
                return flt.def_cls
        return MR.Core.base.BaseBot

    def list(self) -> list[str]:
        return list(self._entries.keys())

    # def load_all(self) -> None:
    #     for entry in self._entries.values():
    #         entry.filters[0].def_cls.load()

    # def save_all(self) -> None:
    #     for entry in self._entries.values():
    #         entry.filters[0].def_cls.save()

    def action(self, msg_event: MsgEvent) -> None:
        """BOT行动循环。"""
        game_work = MR.Core.work.GameWork.from_manager(msg_event)
        bot_mark = msg_event.msg_format("strMrBotMark")
        while not game_work.flag_over and game_work.flag_bot:
            shooter = game_work.shooter
            bot_cls = self.get(game_work.players[shooter]["bot_model"])
            bot_name = game_work.get_name(shooter)
            state = game_work.get_state()
            memory = {}
            while not game_work.flag_over and game_work.shooter == shooter:
                game_work.tmp.clear()
                action = bot_cls.decide(msg_event, state, memory)
                memory = action.memory
                target = game_work.get_target(action.target) if action.target else shooter
                assert target is not None

                if action.type == action.USE_PROP:
                    if target == shooter:
                        game_work.upsert_info(
                            msg_event.msg_format(
                                "strMrBotUsePropToSelf",
                                {"tBotMark": bot_mark, "tBotName": bot_name, "tPropName": action.prop},
                            )
                        )
                    else:
                        game_work.upsert_info(
                            msg_event.msg_format(
                                "strMrBotUsePropToOther",
                                {
                                    "tBotMark": bot_mark,
                                    "tBotName": bot_name,
                                    "tPropName": action.prop,
                                    "tTargetName": game_work.get_name(target),
                                },
                            )
                        )
                    MR.Core.registry.propReg.apply(msg_event, action.prop, shooter, target)
                elif action.type == action.SHOOT_SELF:
                    game_work.upsert_info(msg_event.msg_format("strMrBotShootSelf", {"tBotMark": bot_mark, "tBotName": bot_name}))
                    game_work.shoot(shooter)
                else:
                    game_work.upsert_info(
                        msg_event.msg_format(
                            "strMrBotShootOther",
                            {"tBotMark": bot_mark, "tBotName": bot_name, "tTargetName": game_work.get_name(target)},
                        )
                    )
                    game_work.shoot(target)
                state = game_work.get_state()
                for f, v in memory.items():
                    setattr(state, f, v)
        return


# endregion

command = CommandRegistry()

modeReg = ModeRegistry()
propReg = PropRegistry()
effectReg = EffectRegistry()
botReg = BotRegistry()

modeDef = modeReg.modeDef
propDef = propReg.propDef
effectDef = effectReg.effectDef
botDef = botReg.botDef


def init_after():
    modeReg.init_after()
    propReg.init_after()
    effectReg.init_after()
    botReg.init_after()
