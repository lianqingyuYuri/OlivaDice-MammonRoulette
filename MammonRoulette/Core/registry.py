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

from AmorLib import STRING_ROW, Entry, HandlerFilter, MsgEvent, Registry

import MammonRoulette as MR


# region 指令注册
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

    def search(self, msg_event: MsgEvent):
        """匹配所有过滤器，返回 (handler, groups) 列表。"""
        result = []
        for entry in self.match_handlers(msg_event):
            regex_filter = None
            for flt in entry.filters:
                if isinstance(flt, MsgRegexFilter):
                    regex_filter = flt
                    break
            if regex_filter:
                result.append((entry.key, regex_filter.match.groups() if regex_filter.match else ()))
        return result


command = CommandRegistry()
# endregion


# region 模式注册
class ModeFilter(HandlerFilter[MsgEvent]):
    """按对局当前模式名过滤：对局模式名 == 模式类.name 时放行。"""

    def __init__(self, mode_cls: type[MR.Core.base.BaseMode]):
        self.mode_cls = mode_cls

    def filter(self, msg_event: MsgEvent) -> bool:
        mode_name = msg_event.val.get("game", {}).get("mode", {}).get("name")
        return mode_name is not None and mode_name == self.mode_cls.name


class ModeRegistry(Registry[MsgEvent]):
    """以模式名为键注册模式，模式类挂在过滤器上，运行期按对局模式名派发。"""

    _entries: dict[str, Entry[MsgEvent]]

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
            self.attach(mode_cls.name, ModeFilter(mode_cls))
            return mode_cls

        return decorator

    def get(self, name: str) -> type[MR.Core.base.BaseMode] | None:
        """按模式名取模式类 O(1)"""
        entry = self._entries.get(name)
        if entry is None:
            return None
        filter = entry.filters[0]
        if isinstance(filter, ModeFilter):
            return filter.mode_cls
        return None

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


modeReg = ModeRegistry()
modeDef = modeReg.modeDef
# endregion

# region 道具注册

# endregion

# region 效果注册

# endregion

# region BOT注册

# endregion
