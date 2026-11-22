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
class CommandFilter(HandlerFilter[MsgEvent]):
    """按对局状态与消息正则过滤。"""

    def __init__(self, states: str | STRING_ROW, pattern: str):
        self.states = set((states,) if isinstance(states, str) else states)
        self.pattern = re.compile(pattern)
        self.match = None

    def filter(self, msg_event: MsgEvent) -> bool:
        state = msg_event.val.get("state")
        if state is None or state not in self.states:
            return False
        self.match = self.pattern.search(msg_event.msg)
        return self.match is not None


class CommandRegistry(Registry[MsgEvent]):
    def command(self, states: str | STRING_ROW, pattern: str, helpdoc: str | None = None):
        def decorator(func):
            if helpdoc is not None:
                doc = MR.custom.dictHelpDocTemplate["default"]
                doc["恶赌 命令"] = helpdoc if not doc.get("恶赌 命令") else f"{doc['恶赌 命令']}\n{helpdoc}"
            self.attach(func, CommandFilter(states, pattern))
            return func

        return decorator

    def search(self, msg_event: MsgEvent):
        """按状态与正则匹配，返回 (handler, groups) 列表。"""
        result = []
        for entry in self.match_handlers(msg_event):
            for flt in entry.filters:
                if isinstance(flt, CommandFilter):
                    result.append((entry.key, flt.match.groups() if flt.match else ()))
                    break
        return result


command_reg = CommandRegistry()
command = command_reg.command
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

    def modeDef(self, helpdoc: dict | None = None, strCustom: dict | None = None):
        """注册模式"""
        helpdoc = helpdoc if helpdoc is not None else {}
        strCustom = strCustom if strCustom is not None else {}

        def decorator(mode_cls: type[MR.Core.base.BaseMode]):
            if not mode_cls.name:
                raise ValueError(f"模式类 {mode_cls.__name__} 未定义 name")
            MR.custom.dictHelpDocTemplate["default"].update(helpdoc)
            for field, (note, msg) in strCustom.items():
                MR.custom.dictStrCustomNote[field] = note
                MR.custom.dictStrCustomTemplate["default"][field] = msg
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
        """按当前对局模式名派发生命周期钩子（等价 ModeComp.trigger）。"""
        mode_name = msg_event.val.get("game", {}).get("mode", {}).get("name")
        mode_cls = self.get(mode_name) if mode_name is not None else None
        if mode_cls is None:
            return
        getattr(mode_cls, moment)(msg_event)
        return


mode_reg = ModeRegistry()
modeDef = mode_reg.modeDef
# endregion

# region 道具注册

# endregion

# region 效果注册

# endregion

# region BOT注册

# endregion
