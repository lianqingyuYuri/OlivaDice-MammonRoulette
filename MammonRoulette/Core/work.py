# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/core/work.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

import MammonRoulette as MR

import time
import random
from dataclasses import dataclass

from AmorLib import DataBase, MsgManager

from .base import BaseMode
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
    mode: BaseMode
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

    ammo_live = data_mirror("ammo_live")  # 实弹数
    ammo_blank = data_mirror("ammo_blank")  # 空弹数
    bullet = data_mirror("bullet")  # 当前子弹
    shooter = data_mirror("shooter")  # 枪手
    dmg = modify_mirror("dmg")  # 伤害
    flag_ammo_show = modify_mirror("flag_ammo_show")  # 显示弹药
    flag_bullet_show = modify_mirror("flag_bullet_show")  # 显示子弹

    @property
    def flag_bot(self) -> bool:  # 是否为AI玩家
        return self.players[self.shooter]["bot_model"] is not None

    @property
    def flag_over(self) -> bool:
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
            if note["flag_ammo"]:
                # 子弹
                t_value.update(
                    {"tNowBulletType": self.msg_manager.msg_format("strMrAmmoLive" if self.bullet else "strMrAmmoBlank")}
                )
                t_value.update(
                    {
                        "tGameNowBullet": (
                            self.msg_manager.msg_format("strMrGameNowBulletShow", t_value)
                            if self.flag_bullet_show
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
                            if self.flag_ammo_show
                            else self.msg_manager.msg_format("strMrGameAmmoHide", t_value)
                        )
                    }
                )
            if note["flag_shooter"]:
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
            if not self.flag_over and (note["flag_ammo"] or note["flag_shooter"]):
                msg_reply += "\n" + self.msg_manager.msg_format("strGameReplyNote", t_value)
        else:
            msg_reply = self.reply["only"]
        self.reply.update(
            {"info": [], "note": {"flag_ammo": self.flag_ammo_show or self.flag_bullet_show, "flag_shooter": False}, "only": ""}
        )
        self.tmp.clear()
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
                    "strMrGamblerPropsDraw",
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
        self.chamber()
        random.shuffle(self.order)
        self.shooter = self.order[0]
        self.players[self.shooter]["actions"] = 1
        self.mode.start(self.msg_manager)
        self.reply.update({"info": [], "note": {"flag_ammo": False, "flag_shooter": False}, "only": ""})
        if self.flag_bot:
            MR.Core.comp.BotComp.action(self.msg_manager)
        return

    def chamber(self):
        if self.flag_over:
            return
        if self.ammo_live < 1:
            ammo_live, ammo_blank = self.reload()
        else:
            ammo_live, ammo_blank = self.ammo_live, self.ammo_blank
        self.bullet = random.randint(1, ammo_live + ammo_blank) > ammo_blank
        self.reply["note"]["flag_ammo"] = True
        return

    def reload(self):
        if self.flag_over:
            return 0, 0
        ammo_live, ammo_blank = random.randint(1, 4), random.randint(1, 4)
        self.data["ammo_live"], self.data["ammo_blank"] = ammo_live, ammo_blank
        self.upsert_info(self.msg_manager.msg_format("strMrGameAmmoRanOut"))
        self.handle_event("reload")
        self.reply["note"]["flag_ammo"] = True
        return ammo_live, ammo_blank

    def shoot(self, target):
        source = self.shooter
        self.handle_event(
            "shoot",
            target=target,
            source=source,
            is_shoot_me=target == source,
            dmg=self.dmg,
            dmg_type="",
            consume_action=None,
        )
        target, source, is_shoot_me, dmg, dmg_type, consume_action = (
            self.tmp["target"],
            self.tmp["source"],
            self.tmp["is_shoot_me"],
            self.tmp["dmg"],
            self.tmp["dmg_type"],
            self.tmp["consume_action"],
        )
        pl_target = self.players[target]
        t_reply_id = self.upsert_info()
        if self.bullet:
            if consume_action is None:
                consume_action = 1
            self.ammo_live -= 1
            self.damage(target, dmg, source)
            if self.tmp["new_hp"] > 0:
                self.upsert_info(
                    self.msg_manager.msg_format(
                        "strMrGamblerWasShotWithLiveAmmo",
                        {
                            "tTargetName": pl_target["name"],
                            "tSourceName": self.get_name(source),
                            "tHpOld": self.tmp["old_hp"],
                            "tHpNew": self.tmp["new_hp"],
                        },
                    ),
                    t_reply_id,
                )
        else:
            self.ammo_blank -= 1
            if consume_action is None:
                consume_action = 0 if is_shoot_me else 1
            self.upsert_info(
                self.msg_manager.msg_format(
                    "strMrGamblerWasShotWithBlankAmmo",
                    {
                        "tTargetName": pl_target["name"],
                        "tSourceName": self.get_name(source),
                        "tHpOld": pl_target["hp"],
                        "tHpNew": pl_target["hp"],
                    },
                ),
                t_reply_id,
            )
        self.tmp["consume_action"] = consume_action
        self.chamber()
        self.done()
        return

    def damage(self, target, dmg, source):
        if self.flag_over:
            return
        self.handle_event(
            "damage",
            target=target,
            source=source,
            is_attack_me=target == source,
            dmg=dmg,
            dmg_type=self.tmp.get("dmg_type", ""),
            is_check_dead=self.tmp.get("is_check_dead", True),
        )
        target, source, is_attack_me, dmg, dmg_type, is_check_dead = (
            self.tmp["target"],
            self.tmp["source"],
            self.tmp["is_attack_me"],
            self.tmp["dmg"],
            self.tmp["dmg_type"],
            self.tmp["is_check_dead"],
        )
        pl_target = self.players[target]
        self.tmp["old_hp"] = pl_target["hp"]
        pl_target["hp"] -= dmg
        self.tmp["new_hp"] = pl_target["hp"]
        self.tmp["is_dead"] = False
        if pl_target["hp"] <= 0 and target in self.order and is_check_dead:
            self.tmp["is_dead"] = True
            self.dead(target, source)
        return

    def dead(self, target, source):
        if self.flag_over:
            return
        if not source:
            source = self.shooter
        is_attack_me = self.tmp.get("is_attack_me", target == source)

        pl_target, pl_source = self.players[target], self.players[source]
        if pl_target["surrender"]:  # 投降
            self.upsert_info(self.msg_manager.msg_format("strMrGamblerSurrender", {"tGamblerName": pl_target["name"]}))
        elif is_attack_me:  # 自杀
            pl_target["suicide"] = True
            self.upsert_info(self.msg_manager.msg_format("strMrGamblerSuicide", {"tGamblerName": pl_target["name"]}))
        else:  # 被杀
            pl_source["kills"] += 1
            pl_target["suicide"] = False
            self.upsert_info(
                self.msg_manager.msg_format(
                    "strMrGamblerKilled",
                    {"tTargetName": pl_target["name"], "tSourceName": pl_source["name"]},
                ),
            )
        if target == self.shooter:
            self.switch()
        self.order.remove(target)
        self.handle_event(
            "dead", target=target, source=source, is_attack_me=is_attack_me, check_over=self.tmp.get("check_over", True)
        )
        check_over = self.tmp["check_over"]
        if check_over:
            self.try_over()
        return

    def done(self):
        if self.flag_over:
            return
        self.handle_event("done", consume_action=self.tmp.get("consume_action", 0))
        consume_action = self.tmp["consume_action"]
        pl_shooter = self.players[self.shooter]
        pl_shooter["actions"] -= consume_action
        if pl_shooter["actions"] < 1:
            self.switch()
        if self.flag_bot:
            MR.Core.comp.BotComp.action(self.msg_manager)
        return

    def switch(self):
        shooter = self.shooter
        while True:
            shooter = self.order[(self.order.index(shooter) + 1) % len(self.order)]
            pl_shooter = self.players[shooter]
            pl_shooter["actions"] += 1
            if pl_shooter["actions"] > 0:
                break
        if self.shooter != shooter:
            self.shooter = shooter
            self.reply["note"]["flag_shooter"] = True
            self.handle_event("switch", shooter=shooter, consume_action=0)
        return

    def try_over(self):
        if self.flag_over:
            return True
        self.tmp["check_over"] = True
        flag_over = self.mode.try_over(self.msg_manager)
        if len(self.order) == 1:
            self.upsert_info(self.msg_manager.msg_format("strMrGameOver", {"tWinnerName": self.get_name(self.order[0])}))
            flag_over = True
        elif len(self.order) < 1:
            self.upsert_info(self.msg_manager.msg_format("strMrGameTied"))
            flag_over = True
        if flag_over:
            self.over()
        return flag_over

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
