# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/core/work.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from __future__ import annotations

import MammonRoulette as MR

import time
import random
from dataclasses import dataclass

from AmorLib import DataBase, MsgManager

from .. import config


def data_mirror(key):
    def getter(self):
        return self.data[key]

    def setter(self, value):
        self.data[key] = value

    getter.__name__ = f"get_{key}"
    getter.__qualname__ = f"data_mirror.<locals>.get_{key}"
    setter.__name__ = f"set_{key}"
    setter.__qualname__ = f"data_mirror.<locals>.set_{key}"
    return property(getter, setter)


def modify_mirror(key):
    def getter(self):
        return self.modify[key]

    def setter(self, value):
        self.modify[key] = value

    getter.__name__ = f"get_{key}"
    getter.__qualname__ = f"modify_mirror.<locals>.get_{key}"
    setter.__name__ = f"set_{key}"
    setter.__qualname__ = f"modify_mirror.<locals>.set_{key}"
    return property(getter, setter)


@dataclass
class GameWork:
    # region index
    msg_manager: MsgManager
    mode: MR.Core.base.BaseMode
    game: dict
    data: dict
    reply: dict
    tmp: dict

    modify: dict
    players: dict
    order: list
    props_event: list

    props_pool: list
    props_allow: list
    props_ban: list
    props_limit: int

    ammo_live = data_mirror("ammo_live")  # 实弹
    ammo_blank = data_mirror("ammo_blank")  # 空包弹
    bullet = data_mirror("bullet")  # 当前子弹
    shooter = data_mirror("shooter")  # 枪手
    dmg = modify_mirror("dmg")  # 伤害
    ammo_show = modify_mirror("ammo_show")  # 显示弹药
    bullet_show = modify_mirror("bullet_show")  # 显示子弹

    @property
    def flag_bot(self) -> bool:  # 是否为AI玩家
        return self.players[self.shooter]["bot_model"] is not None

    @property
    def flag_over(self):
        return self.game["over"]

    @classmethod
    def from_manager(cls, msg_manager):
        game = msg_manager.val["game"]
        data = game["data"]
        props = game["mode"]["props"]
        return cls(
            msg_manager=msg_manager,
            mode=MR.Core.comp.ModeComp.get(game["mode"]["name"]),
            game=game,
            data=data,
            reply=game["reply"],
            tmp=game["tmp"],
            modify=data["modify"],
            players=data["players"],
            order=data["order"],
            props_event=data["props_event"],
            props_pool=props["pool"],
            props_allow=props["allow"],
            props_ban=props["ban"],
            props_limit=props["limit"],
        )

    def get_name(self, user_id: str | None = None) -> str:  # 获取玩家昵称
        if not user_id:
            user_id = self.shooter
        return self.players[user_id]["name"]

    def get_target(self, target=None):
        if not target:
            target = self.order[(self.order.index(self.shooter) + 1) % len(self.order)]
        elif target not in self.order:
            target = int(target)
            if target > len(self.order) or target < 1:
                return
            target = self.order[target - 1]
        return target

    # endregion
    # region reply
    def upsert_info(self, info: str = "", info_id: int | None = None) -> int:
        if info_id:
            info_flag = False
            for item in self.reply["info"]:
                if item["id"] == info_id:
                    item["data"] = info
                    info_flag = True
                    break
            if not info_flag:
                self.reply["info"].append({"id": info_id, "data": info})
        else:
            info_id = max((item["id"] for item in self.reply["info"]), default=0) + 1
            self.reply["info"].append({"id": info_id, "data": info})
        return info_id

    def format_reply(self) -> str:  # 格式化回复消息
        if not self.reply["only"]:
            info, note = self.reply["info"], self.reply["note"]
            t_value = {}
            t_value.update({"tInfo": "\n".join([item["data"] for item in info if item["data"]])})
            if note["ammo"]:
                # 子弹
                t_value.update(
                    {"tNowBulletType": self.msg_manager.msg_format("strMrAmmoLive" if self.bullet else "strMrAmmoBlank")}
                )
                t_value.update(
                    {
                        "tGameNowBullet": (
                            self.msg_manager.msg_format("strMrGameNowBulletShow", t_value)
                            if self.bullet_show
                            else self.msg_manager.msg_format("strMrGameNowBulletHide", t_value)
                        )
                    }
                )
                # 弹药
                t_value.update(
                    {
                        "tAmmoLiveCount": self.ammo_live,
                        "tAmmoBlankCount": self.ammo_blank,
                        "tAmmoCount": self.ammo_live + self.ammo_blank,
                    }
                )
                t_value.update(
                    {
                        "tGameAmmo": (
                            self.msg_manager.msg_format("strMrGameAmmoShow", t_value)
                            if self.ammo_show
                            else self.msg_manager.msg_format("strMrGameAmmoHide", t_value)
                        )
                    }
                )
            if note["round"]:
                # 枪手
                t_value.update(
                    {
                        "tShooter": self.msg_manager.msg_format(
                            "strMrGameShooter",
                            {
                                "tGamblerIdx": self.order.index(self.shooter) + 1,
                                "tGamblerName": self.get_name(),
                            },
                        )
                    }
                )
            msg_reply = self.msg_manager.msg_format("strGameReplyInfo", t_value)
            if not self.flag_over and (note["ammo"] or note["round"]):
                msg_reply += "\n" + self.msg_manager.msg_format("strGameReplyNote", t_value)
        else:
            msg_reply = self.reply["only"]
        self.reply.update({"info": [], "note": {"ammo": self.ammo_show or self.bullet_show, "round": False}, "only": ""})
        return msg_reply

    # endregion
    # region 事件
    def get_prop_data(self, prop_id: int | None = None, prop_name: str | None = None):
        search = []
        if prop_id:
            for prop_data in self.props_event:
                if prop_data["id"] == prop_id:
                    search.append(prop_data)
        if prop_name:
            for prop_data in self.props_event:
                if prop_data["name"] == prop_name:
                    search.append(prop_data)
        return search

    def get_effect_data(self, target: str, effect_name: str):
        return self.players[target]["effects_event"].get(effect_name)

    def create_props_event(self, prop_data):
        prop_data["id"] = id(prop_data)
        self.props_event.append(prop_data)
        return

    def create_effects_event(self, target: str, effect_name: str, effect_data: dict):
        self.players[target]["effects_event"][effect_name] = effect_data
        return

    def remove_props_event(self, prop_id: int | None = None, prop_name: str | None = None):
        if not prop_id and not prop_name:
            return
        if prop_id:
            search = prop_id
            search_key = "id"
        else:
            search = prop_name
            search_key = "name"
        for prop_data in reversed(self.props_event):
            if prop_data[search_key] == search:
                MR.Core.comp.PropComp.uninstall(self.msg_manager, prop_data["name"], prop_data)
                self.props_event.remove(prop_data)
        return

    def remove_effects_event(self, effect_name, target, stacks: int = 0):
        effects_event = self.players[target]["effects_event"]
        if effect_name in effects_event:
            effect_data = effects_event[effect_name]
            effect_data["stacks"] -= stacks
            if effect_data["stacks"] <= 0 or stacks == 0:
                MR.Core.comp.EffectComp.uninstall(self.msg_manager, effect_name)
                del effects_event[effect_name]
        return

    def handle_event(self, moment, **kwargs):
        self.tmp.update(kwargs)
        for prop_data in reversed(self.props_event):
            if MR.Core.comp.PropComp.trigger(self.msg_manager, prop_data["name"], moment, prop_data):
                self.remove_props_event(prop_data["id"])
        for prop_data in self.props_event:
            MR.Core.comp.PropComp.sustain(self.msg_manager, prop_data["name"], prop_data)
        for target in self.players:
            effects_event = self.players[target]["effects_event"]
            for effect in list(effects_event.keys()):
                if MR.Core.comp.EffectComp.trigger(self.msg_manager, effect, moment, target, effects_event[effect]):
                    self.remove_effects_event(effect, target, 0)
        MR.Core.comp.ModeComp.trigger(self.msg_manager, moment)
        return

    # endregion
    # region 道具
    def get_prop(self, user_id, prop):
        pl_props = self.players[user_id]["props"]
        if self.props_limit > 0 and len(pl_props) >= self.props_limit:
            return None
        elif prop in self.props_ban:
            prop = random.choice(self.props_pool)
        elif not MR.Core.comp.PropComp.get(prop).allow_flag and prop not in self.props_allow:
            prop = random.choice(self.props_pool)
        pl_props.append(prop)
        return prop

    def remove_prop(self, user_id, prop):
        pl_props = self.players[user_id]["props"]
        if prop not in pl_props:
            return False
        pl_props.remove(prop)
        return True

    def draw_prop(self, user_id, count, pool=None):
        t_pool = pool or self.props_pool
        t_draw_props = []
        for _ in range(count):
            prop = random.choice(t_pool)
            actual_prop = self.get_prop(user_id, prop)
            if not actual_prop:
                break
            t_draw_props.append(actual_prop)
        if t_draw_props:
            link = self.msg_manager.msg_format("strMrLink")
            self.upsert_info(
                self.msg_manager.msg_format(
                    "strMrGamblerDrawnProps",
                    {
                        "tGamblerName": self.get_name(user_id),
                        "tDrawnProps": link.join(t_draw_props),
                    },
                ),
            )
        return

    # endregion
    # region action
    def join(self, user_id, bot_model=None):
        if bot_model is None:
            with DataBase(config.DB_PATH) as db:
                name = db.select("gambler", "name", "user_id = ?", user_id)[0][0]
        else:
            name = bot_model
        self.order.append(user_id)
        self.players[user_id] = {
            "name": name,
            "hp": 3,
            "actions": 0,
            "props": [],
            "kills": 0,
            "suicide": False,
            "surrender": False,
            "points_mult": 0,
            "effects_event": {},
            "bot_model": bot_model,
        }
        self.mode.join(self.msg_manager, user_id)
        return

    def start(self):
        self.game["start"] = True
        self.game["expireTime"] = int(time.time()) // 60 + 120
        self.chamber_round()
        random.shuffle(self.order)
        self.shooter = self.order[0]
        self.players[self.shooter]["actions"] = 1
        self.mode.start(self.msg_manager)
        self.reply.update({"info": [], "note": {"ammo": False, "round": False}, "only": ""})
        if self.flag_bot:
            MR.Core.comp.BotComp.action(self.msg_manager)
        return

    def chamber_round(self):
        if self.flag_over:
            return
        if self.data["ammo_live"] < 1:
            ammo_live, ammo_blank = self.reload()
        else:
            ammo_live, ammo_blank = self.data["ammo_live"], self.data["ammo_blank"]
        self.data["bullet"] = random.randint(1, ammo_live + ammo_blank) > ammo_blank
        self.reply["note"]["ammo"] = True
        return

    def reload(self):
        if self.flag_over:
            return 0, 0
        ammo_live, ammo_blank = random.randint(1, 4), random.randint(1, 4)
        self.data["ammo_live"], self.data["ammo_blank"] = ammo_live, ammo_blank
        self.upsert_info(self.msg_manager.msg_format("strMrGameAmmoRanOut"))
        self.handle_event("reload")
        return ammo_live, ammo_blank

    def shoot(self, target):
        dmg_type = ""
        is_attack_me = target == self.shooter
        murderer = self.shooter
        consume_action = None
        self.handle_event(
            "shoot",
            target=target,
            dmg=self.dmg,
            dmg_type=dmg_type,
            is_attack_me=is_attack_me,
            murderer=murderer,
            consume_action=consume_action,
        )
        target, dmg, dmg_type, is_attack_me, murderer, consume_action = (
            self.tmp["target"],
            self.tmp["dmg"],
            self.tmp["dmg_type"],
            self.tmp["is_attack_me"],
            self.tmp["murderer"],
            self.tmp["consume_action"],
        )
        pl_target = self.players[target]
        t_reply_id = self.upsert_info()
        if self.data["bullet"]:
            if consume_action is None:
                consume_action = 1
            self.ammo_live -= 1
            self.damage(target, dmg, murderer)
            hp_before, hp_now = self.tmp["hp_before"], self.tmp["hp_now"]
            if self.tmp["hp_now"] > 0:
                self.upsert_info(
                    self.msg_manager.msg_format(
                        "strMrGamblerWasAmmoLiveShot",
                        {
                            "tGamblerName": pl_target["name"],
                            "tHpBefore": hp_before,
                            "tHpNow": hp_now,
                        },
                    ),
                    t_reply_id,
                )
        else:
            self.ammo_blank -= 1
            if consume_action is None:
                consume_action = 0 if is_attack_me else 1
            self.upsert_info(
                self.msg_manager.msg_format(
                    "strMrGamblerWasAmmoBlankShot",
                    {
                        "tGamblerName": pl_target["name"],
                        "tHpBefore": pl_target["hp"],
                        "tHpNow": pl_target["hp"],
                    },
                ),
                t_reply_id,
            )
        self.tmp["consume_action"] = consume_action
        self.chamber_round()
        self.end_round()
        return

    def damage(self, target, dmg, murderer):
        if self.flag_over:
            return
        dmg_type = self.tmp.get("dmg_type", "")
        check_dead = self.tmp.get("check_dead", True)
        self.handle_event(
            "damage",
            target=target,
            dmg=dmg,
            murderer=murderer,
            dmg_type=dmg_type,
            check_dead=check_dead,
        )
        target, dmg, murderer, dmg_type, check_dead = (
            self.tmp["target"],
            self.tmp["dmg"],
            self.tmp["murderer"],
            self.tmp["dmg_type"],
            self.tmp["check_dead"],
        )
        pl_target = self.players[target]
        self.tmp["hp_before"] = pl_target["hp"]
        pl_target["hp"] -= dmg
        self.tmp["hp_now"] = pl_target["hp"]
        if pl_target["hp"] <= 0 and target in self.order and check_dead:
            self.dead(target, murderer)
        return

    def dead(self, target, murderer):
        if self.flag_over:
            return
        if not murderer:
            murderer = self.shooter
        pl_target, pl_murderer = self.players[target], self.players[murderer]
        name = pl_target["name"]
        if self.players[target]["surrender"]:
            self.upsert_info(self.msg_manager.msg_format("strMrGamblerSurrender", {"tGamblerName": name}))
        elif target == murderer:
            pl_target["suicide"] = True
            self.upsert_info(
                self.msg_manager.msg_format("strMrGamblerSuicide", {"tGamblerName": name}),
            )
        else:
            pl_murderer["kills"] += 1
            pl_target["suicide"] = False
            self.upsert_info(
                self.msg_manager.msg_format(
                    "strMrGamblerKilled",
                    {"tGamblerName": name, "tMurdererName": pl_murderer["name"]},
                ),
            )
        if target == self.shooter:
            self.switch()
        self.order.remove(target)
        check_over = self.tmp.get("check_over", True)
        self.handle_event("dead", target=target, murderer=murderer, check_over=check_over)
        check_over = self.tmp["check_over"]
        if check_over:
            self.try_over()
        return

    def end_round(self):
        if self.flag_over:
            return
        self.handle_event("end_round")
        consume_action = self.tmp.get("consume_action") or 0
        pl_shooter = self.players[self.shooter]
        pl_shooter["actions"] -= consume_action
        if pl_shooter["actions"] < 1:
            self.switch()
        if self.flag_bot:
            MR.Core.comp.BotComp.action(self.msg_manager)
        return

    def switch(self):
        self.tmp["consume_action"] = 0
        shooter = self.data["shooter"]
        while True:
            shooter = self.order[(self.order.index(shooter) + 1) % len(self.order)]
            pl_shooter = self.players[shooter]
            pl_shooter["actions"] += 1
            if pl_shooter["actions"] > 0:
                break
        if self.shooter != shooter:
            self.shooter = shooter
            pl_shooter = self.players[shooter]
            self.reply["note"]["round"] = True
            self.handle_event("switch")
        return

    def try_over(self):
        if self.flag_over:
            return True
        self.tmp["check_over"] = True
        if len(self.order) == 1:
            self.upsert_info(self.msg_manager.msg_format("strMrGameEnd", {"tWinnerName": self.get_name(self.order[0])}))
            self.over()
            return True
        elif len(self.order) < 1:
            self.upsert_info(self.msg_manager.msg_format("strMrGameTied"))
            self.over()
            return True
        return False

    def over(self):
        self.game["over"] = True
        with DataBase(config.DB_PATH) as db:
            for pl in self.players.keys():
                if self.players[pl]["bot_model"] is None:
                    continue
                pl_target = self.players[pl]
                mult = pl_target["points_mult"] + pl_target["kills"]
                if pl not in self.order:
                    mult -= 1
                    wl = "losses"
                else:
                    mult += 1
                    wl = "wins"
                db.update(
                    "gambler",
                    {
                        "points": self.game["mode"]["points"] * mult,
                        "kills": pl_target["kills"],
                        "suicide": 1 if pl_target["suicide"] else 0,
                        "surrender": 1 if pl_target["surrender"] else 0,
                        wl: 1,
                    },
                    "user_id = ?",
                    pl,
                    increment=("points", "kills", "suicide", "surrender", wl),
                )
        return

    # endregion


# class RegGameWork:
#     # region Base
#     @staticmethod
#     def get_name(game, user_id: str | None = None) -> str:  # 获取玩家昵称
#         data = game["data"]
#         if not user_id:
#             user_id = data["shooter"]
#         return data["players"][user_id]["name"]

#     @staticmethod
#     def get_index(msg_manager):
#         game: dict = msg_manager.val["game"]
#         data: dict = game["data"]
#         reply: dict = game["reply"]
#         tmp: dict = game["tmp"]
#         modify: dict = data["modify"]
#         players: dict = data["players"]
#         order: list = data["order"]
#         shooter: str = data["shooter"]
#         bullet: bool = data["bullet"]
#         return game, data, reply, tmp, modify, players, order, shooter, bullet

#     @staticmethod
#     def is_bot(game, user_id: str) -> bool:  # 是否为AI玩家
#         return game["data"]["players"][user_id]["bot_model"] != None

#     @staticmethod
#     def reply_info(msg_manager, info: str = "", info_id: int | None = None):
#         reply = msg_manager.val["game"]["reply"]
#         if info_id:
#             info_flag = False
#             for item in reply["info"]:
#                 if item["id"] == info_id:
#                     item["data"] = info
#                     info_flag = True
#                     break
#             if not info_flag:
#                 reply["info"].append({"id": info_id, "data": info})
#         else:
#             info_id = max((item["id"] for item in reply["info"]), default=0) + 1
#             reply["info"].append({"id": info_id, "data": info})
#         return info_id

#     @staticmethod
#     def format_reply(msg_manager) -> str:  # 格式化回复消息
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if not reply["only"]:
#             info, note = reply["info"], reply["note"]
#             t_value = {}
#             t_value.update({"tInfo": "\n".join([item["data"] for item in info if item["data"]])})
#             if note["ammo"]:
#                 # 子弹
#                 t_value.update({"tNowBulletType": msg_manager.msg_format("strMrAmmoLive" if bullet else "strMrAmmoBlank")})
#                 t_value.update(
#                     {
#                         "tGameNowBullet": (
#                             msg_manager.msg_format("strMrGameNowBulletShow", t_value)
#                             if modify["bullet_show"]
#                             else msg_manager.msg_format("strMrGameNowBulletHide", t_value)
#                         )
#                     }
#                 )
#                 # 弹药
#                 ammo_live, ammo_blank = data["ammo_live"], data["ammo_blank"]
#                 t_value.update(
#                     {
#                         "tAmmoLiveCount": ammo_live,
#                         "tAmmoBlankCount": ammo_blank,
#                         "tAmmoCount": ammo_live + ammo_blank,
#                     }
#                 )
#                 t_value.update(
#                     {
#                         "tGameAmmo": (
#                             msg_manager.msg_format("strMrGameAmmoShow", t_value)
#                             if modify["ammo_show"]
#                             else msg_manager.msg_format("strMrGameAmmoHide", t_value)
#                         )
#                     }
#                 )
#             if note["round"]:
#                 # 枪手
#                 t_value.update(
#                     {
#                         "tShooter": msg_manager.msg_format(
#                             "strMrGameShooter",
#                             {
#                                 "tGamblerIdx": order.index(shooter) + 1,
#                                 "tGamblerName": players[shooter]["name"],
#                             },
#                         )
#                     }
#                 )
#             msg_reply = msg_manager.msg_format("strGameReplyInfo", t_value)
#             if not game["over"] and (note["ammo"] or note["round"]):
#                 msg_reply += "\n" + msg_manager.msg_format("strGameReplyNote", t_value)
#         else:
#             msg_reply = reply["only"]
#         reply.update(
#             {
#                 "info": [],
#                 "note": {
#                     "ammo": modify["ammo_show"] or modify["bullet_show"],
#                     "round": False,
#                 },
#                 "only": "",
#             }
#         )
#         return msg_reply

#     # endregion
#     # region 事件
#     @staticmethod
#     def get_prop_data(msg_manager, prop_id: int | None = None, prop_name: str | None = None):
#         game = msg_manager.val["game"]
#         search = []
#         if prop_id:
#             for prop_data in game["data"]["props_event"]:
#                 if prop_data["id"] == prop_id:
#                     search.append(prop_data)
#         if prop_name:
#             for prop_data in game["data"]["props_event"]:
#                 if prop_data["name"] == prop_name:
#                     search.append(prop_data)
#         return search

#     @staticmethod
#     def get_effect_data(msg_manager, target: str, effect: str):
#         return msg_manager.val["game"]["data"]["players"][target]["effects_event"].get(effect)

#     @staticmethod
#     def create_props_event(msg_manager, prop_data):
#         prop_data["id"] = id(prop_data)
#         msg_manager.val["game"]["data"]["props_event"].append(prop_data)

#     @staticmethod
#     def create_effects_event(msg_manager, target: str, effect: str, effect_data: dict):
#         msg_manager.val["game"]["data"]["players"][target]["effects_event"][effect] = effect_data

#     @staticmethod
#     def remove_props_event(msg_manager, prop_id: int | None = None, prop_name: str | None = None):
#         if not prop_id and not prop_name:
#             return
#         search = prop_id if prop_id else prop_name
#         search_key = "id" if prop_id else "name"
#         props_event = msg_manager.val["game"]["data"]["props_event"]
#         for prop_data in reversed(props_event):
#             if prop_data[search_key] == search:
#                 MR.Core.comp.PropComp.uninstall(msg_manager, prop_data["name"], prop_data)
#                 props_event.remove(prop_data)
#         return

#     @staticmethod
#     def remove_effects_event(msg_manager, effect, target, stacks: int = 0):
#         effects_event = msg_manager.val["game"]["data"]["players"][target]["effects_event"]
#         effect_data = effects_event[effect]
#         effect_data["stacks"] -= stacks
#         if effect_data["stacks"] <= 0 or stacks == 0:
#             MR.Core.comp.EffectComp.uninstall(msg_manager, effect)
#             del effects_event[effect]
#         return

#     @classmethod
#     def handle_event(cls, msg_manager, moment, **kwargs):
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         tmp.update(kwargs)
#         props_event = data["props_event"]
#         for prop_data in reversed(props_event):
#             if MR.Core.comp.PropComp.trigger(msg_manager, prop_data["name"], moment, prop_data):
#                 cls.remove_props_event(msg_manager, prop_data["id"])
#         for prop_data in props_event:
#             MR.Core.comp.PropComp.sustain(msg_manager, prop_data["name"], prop_data)
#         for target in players:
#             effects_event = players[target]["effects_event"]
#             for effect in list(effects_event.keys()):
#                 if MR.Core.comp.EffectComp.trigger(msg_manager, effect, moment, target, effects_event[effect]):
#                     cls.remove_effects_event(msg_manager, effect, target, 0)
#         MR.Core.comp.ModeComp.trigger(msg_manager, moment)
#         return

#     # endregion
#     # region 道具
#     @staticmethod
#     def get_prop(game, user_id, prop):  # 获取道具
#         mode_props = game["mode"]["props"]
#         mode_limit = mode_props["limit"]
#         pl_props = game["data"]["players"][user_id]["props"]
#         if mode_limit > 0 and len(pl_props) >= mode_limit:
#             return None
#         elif prop in mode_props["ban"]:
#             prop = random.choice(mode_props["pool"])
#         elif prop not in mode_props["allow"] and not MR.Core.comp.PropComp.get(prop).allow_flag:
#             prop = random.choice(mode_props["pool"])
#         pl_props.append(prop)
#         return prop

#     @staticmethod
#     def remove_prop(game, user_id, prop):  # 删除道具
#         pl_props = game["data"]["players"][user_id]["props"]
#         if prop not in pl_props:
#             return False
#         pl_props.remove(prop)
#         return True

#     @classmethod
#     def draw_prop(cls, msg_manager, user_id, count, prop_pool=None):  # 抽取道具
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         prop_pool = prop_pool or game["mode"]["props"]["pool"]
#         draw_props = []
#         for _ in range(count):
#             prop = random.choice(prop_pool)
#             actual_prop = cls.get_prop(game, user_id, prop)
#             if not actual_prop:
#                 break
#             draw_props.append(actual_prop)
#         if draw_props:
#             link = msg_manager.msg_format("strMrLink")
#             cls.reply_info(
#                 msg_manager,
#                 msg_manager.msg_format(
#                     "strMrGamblerDrawnProps",
#                     {
#                         "tGamblerName": cls.get_name(game, user_id),
#                         "tDrawnProps": link.join(draw_props),
#                     },
#                 ),
#             )
#         return

#     # endregion
#     # region action
#     @classmethod
#     def join(cls, msg_manager, user_id, bot_model=None):
#         """添加一名玩家."""
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if bot_model is None:
#             with DataBase(config.DB_PATH) as db:
#                 name = db.select("gambler", "name", "user_id = ?", user_id)[0][0]
#         else:
#             name = bot_model
#         order.append(user_id)
#         data["players"][user_id] = {
#             "name": name,
#             "hp": 3,
#             "actions": 0,
#             "props": [],
#             "kills": 0,
#             "suicide": False,
#             "surrender": False,
#             "points_mult": 0,
#             "effects_event": {},
#             "bot_model": bot_model,
#         }
#         MR.Core.comp.ModeComp.get(game["mode"]["name"]).join(msg_manager, user_id)
#         return

#     @classmethod
#     def start(cls, msg_manager):
#         """对局开始"""
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         game["start"] = True
#         game["expireTime"] = 0
#         cls.bullet(msg_manager)
#         random.shuffle(order)
#         shooter = order[0]
#         data["shooter"] = shooter
#         data["players"][shooter]["actions"] = 1
#         MR.Core.comp.ModeComp.get(game["mode"]["name"]).start(msg_manager)
#         reply.update({"info": [], "note": {"ammo": False, "round": False}, "only": ""})
#         modify["flag_bot"] = cls.is_bot(game, shooter)
#         MR.Core.comp.BotComp.action(msg_manager)
#         return

#     @classmethod
#     def bullet(cls, msg_manager):  # 刷新子弹
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if game["over"]:
#             return
#         if data["ammo_live"] < 1:
#             ammo_live, ammo_blank = cls.reload(msg_manager)
#         else:
#             ammo_live, ammo_blank = data["ammo_live"], data["ammo_blank"]
#         ammo = ammo_live + ammo_blank
#         data["bullet"] = random.randint(1, ammo) > ammo_blank
#         reply["note"]["ammo"] = True
#         return

#     @classmethod
#     def reload(cls, msg_manager):  # 装弹
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         cls.handle_event(msg_manager, "reload")
#         ammo_live, ammo_blank = random.randint(1, 4), random.randint(1, 4)
#         data["ammo_live"], data["ammo_blank"] = ammo_live, ammo_blank
#         cls.reply_info(msg_manager, msg_manager.msg_format("strMrGameAmmoRanOut"))
#         return ammo_live, ammo_blank

#     @classmethod
#     def shoot(cls, msg_manager, target):  # 开枪
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         dmg_type = ""
#         is_attack_me = target == shooter
#         murderer = shooter
#         consume_action = None
#         cls.handle_event(
#             msg_manager,
#             "shoot",
#             target=target,
#             dmg=modify["dmg"],
#             dmg_type=dmg_type,
#             is_attack_me=is_attack_me,
#             murderer=murderer,
#             consume_action=consume_action,
#         )
#         target, dmg, dmg_type, is_attack_me, murderer, consume_action = (
#             tmp["target"],
#             tmp["dmg"],
#             tmp["dmg_type"],
#             tmp["is_attack_me"],
#             tmp["murderer"],
#             tmp["consume_action"],
#         )
#         pl_target = players[target]
#         reply_id = cls.reply_info(msg_manager)
#         if data["bullet"]:
#             if consume_action is None:
#                 consume_action = 1
#             tmp["consume_action"] = consume_action
#             data["ammo_live"] -= 1
#             cls.damage(msg_manager, target, dmg, murderer)
#             hp_before, hp_now = tmp["hp_before"], tmp["hp_now"]
#             if tmp["hp_now"] > 0:
#                 cls.reply_info(
#                     msg_manager,
#                     msg_manager.msg_format(
#                         "strMrGamblerWasAmmoLiveShot",
#                         {
#                             "tGamblerName": pl_target["name"],
#                             "tHpBefore": hp_before,
#                             "tHpNow": hp_now,
#                         },
#                     ),
#                     reply_id,
#                 )
#         else:
#             data["ammo_blank"] -= 1
#             if consume_action is None:
#                 consume_action = 0 if is_attack_me else 1
#             tmp["consume_action"] = consume_action
#             cls.reply_info(
#                 msg_manager,
#                 msg_manager.msg_format(
#                     "strMrGamblerWasAmmoBlankShot",
#                     {
#                         "tGamblerName": pl_target["name"],
#                         "tHpBefore": pl_target["hp"],
#                         "tHpNow": pl_target["hp"],
#                     },
#                 ),
#                 reply_id,
#             )
#         cls.bullet(msg_manager)
#         cls.end_round(msg_manager)
#         return

#     @classmethod
#     def damage(cls, msg_manager, target, dmg, murderer):  # 受伤
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if game["over"]:
#             return
#         dmg_type = tmp.get("dmg_type", "")
#         check_over = tmp.get("check_over", True)
#         cls.handle_event(
#             msg_manager,
#             "damage",
#             target=target,
#             dmg=dmg,
#             murderer=murderer,
#             dmg_type=dmg_type,
#             check_over=check_over,
#         )
#         target, dmg, murderer, dmg_type, check_over = (
#             tmp["target"],
#             tmp["dmg"],
#             tmp["murderer"],
#             tmp["dmg_type"],
#             tmp["check_over"],
#         )
#         pl_target = players[target]
#         tmp["hp_before"] = pl_target["hp"]
#         pl_target["hp"] -= dmg
#         tmp["hp_now"] = pl_target["hp"]
#         if pl_target["hp"] <= 0 and target in order:
#             cls.dead(msg_manager, target, murderer)
#         return

#     @classmethod
#     def dead(cls, msg_manager, target, murderer):  # 死亡
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if game["over"]:
#             return
#         if not murderer:
#             murderer = shooter
#         pl_target, pl_murderer = players[target], players[murderer]
#         name = pl_target["name"]
#         if players[target]["surrender"]:
#             RegGameWork.reply_info(msg_manager, msg_manager.msg_format("strMrGamblerSurrender", {"tGamblerName": name}))
#         elif target == murderer:
#             pl_target["suicide"] = True
#             cls.reply_info(
#                 msg_manager,
#                 msg_manager.msg_format("strMrGamblerSuicide", {"tGamblerName": name}),
#             )
#         else:
#             pl_murderer["kills"] += 1
#             pl_target["suicide"] = False
#             cls.reply_info(
#                 msg_manager,
#                 msg_manager.msg_format(
#                     "strMrGamblerKilled",
#                     {"tGamblerName": name, "tMurdererName": pl_murderer["name"]},
#                 ),
#             )
#         if target == shooter:
#             cls.switch(msg_manager)
#             tmp["consume_action"] = 0
#         order.remove(target)
#         check_over = tmp.get("check_over", True)
#         cls.handle_event(msg_manager, "dead", target=target, murderer=murderer, check_over=check_over)
#         check_over = tmp["check_over"]
#         if check_over:
#             cls.is_over(msg_manager)
#         return

#     @classmethod
#     def is_over(cls, msg_manager):  # 游戏是否结束
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if game["over"]:
#             return True
#         tmp["check_over"] = True
#         if len(order) == 1:
#             cls.reply_info(
#                 msg_manager,
#                 msg_manager.msg_format("strMrGameEnd", {"tWinnerName": cls.get_name(game, order[0])}),
#             )
#             cls.over(msg_manager)
#             return True
#         elif len(order) < 1:
#             cls.reply_info(
#                 msg_manager,
#                 msg_manager.msg_format("strMrGameTied"),
#             )
#             cls.over(msg_manager)
#             return True
#         return False

#     @classmethod
#     def end_round(cls, msg_manager):  # 回合结束
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         if game["over"]:
#             return
#         cls.handle_event(msg_manager, "end_round")
#         consume_action = tmp.get("consume_action") or 0
#         pl_shooter = players[shooter]
#         pl_shooter["actions"] -= consume_action
#         if pl_shooter["actions"] < 1:
#             cls.switch(msg_manager)
#         shooter = data["shooter"]
#         modify["flag_bot"] = cls.is_bot(game, shooter)
#         MR.Core.comp.BotComp.action(msg_manager)
#         return

#     @classmethod
#     def switch(cls, msg_manager):  # 换人
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         while True:
#             shooter = order[(order.index(shooter) + 1) % len(order)]
#             pl_shooter = players[shooter]
#             pl_shooter["actions"] += 1
#             if pl_shooter["actions"] > 0:
#                 break
#         if shooter != data["shooter"]:
#             data["shooter"] = shooter
#             pl_shooter = players[shooter]
#             reply["note"]["round"] = True
#             cls.handle_event(msg_manager, "switch")
#         return

#     @classmethod
#     def over(cls, msg_manager):  # 结算
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         game["over"] = True
#         with DataBase(config.DB_PATH) as db:
#             for pl in players.keys():
#                 if cls.is_bot(game, pl):
#                     continue
#                 pl_target = players[pl]
#                 mult = pl_target["points_mult"] + pl_target["kills"]
#                 if pl not in order:
#                     mult -= 1
#                     wl = "losses"
#                 else:
#                     mult += 1
#                     wl = "wins"
#                 db.update(
#                     "gambler",
#                     {
#                         "points": game["mode"]["points"] * mult,
#                         "kills": pl_target["kills"],
#                         "suicide": 1 if pl_target["suicide"] else 0,
#                         "surrender": 1 if pl_target["surrender"] else 0,
#                         wl: 1,
#                     },
#                     "user_id = ?",
#                     pl,
#                     increment=("points", "kills", "suicide", "surrender", wl),
#                 )
#         return

#     # endregion
