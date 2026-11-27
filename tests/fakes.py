# -*- encoding: utf-8 -*-
"""轻量测试假对象与对局构造工具。

这里的 FakeMsgEvent / FakePluginEvent 只实现被测代码用到的接口，
避免在单元测试中构造完整的 OlivOS / OlivaDiceCore 事件对象。
"""

import re

import MammonRoulette as MR


class RandSeq:
    """按队列返回确定性的随机数（被裁剪到 [a, b] 内）。"""

    def __init__(self, values, default=1):
        self.values = list(values)
        self.default = default

    def __call__(self, a, b):
        value = self.values.pop(0) if self.values else self.default
        return min(max(value, a), b)


class FakeMsgEvent:
    """模拟 MammonRoulette 用到的 MsgEvent 接口。"""

    def __init__(self, val, msg="", user_id="u1", group_id="g1", bot_hash="default", allow_reply=True):
        self.val = val
        self.msg = msg
        self.user_id = user_id
        self.group_id = group_id
        self.bot_hash = bot_hash
        self.flags = {"is_group": bool(group_id)}
        self.allow_reply = allow_reply

    def msg_format(self, custom, t_value=None, flagCross=True, flagSplit=False):
        if t_value is None:
            t_value = {}
        template = MR.custom.dictStrCustomTemplate.get("default", {}).get(custom, custom)
        if flagSplit and isinstance(template, str) and "|" in template:
            template = template.split("|")[0]

        def replace(match):
            key = match.group(1)
            return str(t_value.get(key, ""))

        return re.sub(r"\{([^{}]*)\}", replace, template)


class FakePluginEvent:
    """模拟插件事件中 handler 使用到的 reply 接口。"""

    def __init__(self, **kwargs):
        self.replies = []
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reply(self, msg):
        self.replies.append(msg)
        return msg


def build_game(mode_name="经典", seats=2, start=False, over=False):
    """按 template.py 的结构构造一个完整对局字典。"""
    mode_cfg = MR.custom.dictModeCustom["default"][mode_name]
    return {
        "start": start,
        "over": over,
        "expireTime": 999999,
        "seats": seats,
        "mode": {
            "name": mode_name,
            "points": mode_cfg["points"],
            "props": {
                "pool": list(mode_cfg["props"]["pool"]),
                "allowed": list(mode_cfg["props"]["allowed"]),
                "banned": list(mode_cfg["props"]["banned"]),
                "limit": mode_cfg["props"]["limit"],
            },
        },
        "data": {
            "ammo_live": 0,
            "ammo_blank": 0,
            "bullet": False,
            "shooter": "",
            "order": [],
            "players": {},
            "modify": {
                "dmg": mode_cfg["modify"]["dmg"],
                "ammo_visible": bool(mode_cfg["modify"]["ammo_visible"]),
                "bullet_visible": bool(mode_cfg["modify"]["bullet_visible"]),
            },
            "props_event": [],
        },
        "reply": {
            "info": [],
            "below": {"show_ammo": False, "show_shooter": False},
            "override": "",
        },
        "tmp": {},
        "IdStore": 0,
    }


def add_player(game, user_id, name=None, hp=3, bot_model=None, actions=0):
    """直接向对局写入一名玩家，不经过数据库。"""
    game["data"]["order"].append(user_id)
    game["data"]["players"][user_id] = {
        "name": name if name is not None else user_id,
        "hp": hp,
        "actions": actions,
        "props": [],
        "kills": 0,
        "suicide": False,
        "surrender": False,
        "points_mult": 0,
        "effects_event": {},
        "bot_model": bot_model,
    }
    return game["data"]["players"][user_id]


def msg_event_for(game, **kwargs):
    """构造携带指定对局的 FakeMsgEvent。"""
    return FakeMsgEvent(val={"game": game, "state": kwargs.pop("state", "ob")}, **kwargs)
