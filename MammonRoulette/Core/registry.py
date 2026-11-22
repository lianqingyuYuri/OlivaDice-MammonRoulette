# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Core/event.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

import re

from AmorLib import STRING_ROW, HandlerFilter, MsgEvent, Registry

import MammonRoulette as MR


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
        if helpdoc is not None:
            doc = MR.custom.dictHelpDocTemplate["default"]
            doc["恶赌 命令"] = helpdoc if not doc.get("恶赌 命令") else f"{doc['恶赌 命令']}\n{helpdoc}"

        def decorator(func):
            self.attach(func, CommandFilter(states, pattern))
            return func

        return decorator

    def search(self, msg_event: MsgEvent):
        """按状态与正则匹配，返回 (handler, groups) 列表。"""
        result = []
        for entry in self.match_handlers(msg_event):
            for flt in entry.filters:
                if isinstance(flt, CommandFilter):
                    result.append((entry.func, flt.match.groups() if flt.match else ()))
                    break
        return result


command_reg = CommandRegistry()
command = command_reg.command
