# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Defs/mode.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

import random

from ..msgCustom import dictModeCustom, dictDefsNote
from ..Core.base import BaseMode
from ..Core.comp import ModeComp
from ..Core.work import GameWork


class 经典(ModeComp, BaseMode):
    name = "经典"
    brief = (
        "〈赏金〉50"
        "\n〈血量〉每名玩家4hp."
        "\n〈道具池〉(上限6)"
        "\n{手铐,锯子,花生,巧克力,香烟,红牛,邀请函,放大镜}"
        "\n〔机制〕 "
        "\n1. 游戏开始时, 首发玩家抽取 2 个道具, 非首发玩家抽取 1 个道具;"
        "\n2. 玩家回合开始时抽取 2 个道具."
    )
    points = 50

    class props(BaseMode.props):
        pool = ("手铐", "锯子", "花生", "巧克力", "香烟", "红牛", "邀请函", "放大镜")
        limit = 6

    @classmethod
    def start(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        for pl in game_work.order[1:]:
            game_work.draw_prop(pl, 1)
        game_work.draw_prop(game_work.shooter, 2)

    @classmethod
    def join(cls, msg_manager, user_id):
        msg_manager.val["game"]["data"]["players"][user_id]["hp"] = 4

    # 换人
    @classmethod
    def switch(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        game_work.draw_prop(game_work.shooter, 2)


class 道具(ModeComp, BaseMode):
    name = "道具"
    brief = (
        "〈赏金〉40"
        "\n〈血量〉前3名玩家5hp, 其余玩家6hp."
        "\n〈道具池〉(上限16)"
        "\n{手铐,锯子,邀请函,花生,巧克力,香烟,红牛,放大镜,口红,扑克,转盘,牛奶}"
        "\n〔机制〕"
        "\n1. 装弹时所有玩家抽取 4 个道具."
    )
    points = 40

    class props(BaseMode.props):
        pool = (
            "手铐",
            "锯子",
            "邀请函",
            "花生",
            "巧克力",
            "香烟",
            "红牛",
            "放大镜",
            "口红",
            "扑克",
            "转盘",
            "牛奶",
            "止疼药",
            "烟花",
        )
        limit = 16

    @classmethod
    def join(cls, msg_manager, user_id):
        game_work = GameWork.from_manager(msg_manager)
        game_work.players[user_id]["hp"] = 5 if len(game_work.order) < 4 else 6

    # 装弹
    @classmethod
    def reload(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        for pl in game_work.order:
            game_work.draw_prop(pl, 4)


class 金币(ModeComp, BaseMode):
    name = "金币"
    brief = (
        "〈赏金〉60"
        "\n〈血量〉每名玩家5hp."
        "\n〈道具池(上限12)〉\\{金币\\}"
        "\n〔机制〕"
        "\n1. 回合开始时获得 1 枚金币;"
        "\n2. 玩家血量首次低至 2 时, 获得 1 枚金币."
    )
    points = 60
    reply = (
        ("strMrModeGold_1", "金币模式 机制2的回复词", "金光乍現！一枚金幣落入{tGamblerName}手中."),
        ("strMrModeGold_2", "金币模式 机制2的回复词", "金光乍現！一枚含金量0%的金幣?落入{tGamblerName}手中."),
    )

    class props(BaseMode.props):
        pool = ("金币",)
        limit = 12

    @classmethod
    def start(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        game_work.draw_prop(game_work.shooter, 1)

    @classmethod
    def join(cls, msg_manager, user_id):
        msg_manager.val["game"]["data"]["players"][user_id]["hp"] = 5

    # 换人
    @classmethod
    def switch(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        game_work.draw_prop(game_work.shooter, 1)

    # 受伤
    @classmethod
    def damage(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        modify, tmp = game_work.modify, game_work.tmp
        target, dmg = tmp["target"], tmp["dmg"]
        comp = modify.setdefault("金币", [])
        if target not in comp and game_work.players[target]["hp"] - dmg <= 2:
            t_value = {"tGamblerName": game_work.get_name(target)}
            if game_work.get_prop(target, "金币"):
                msg_reply = msg_manager.msg_format("strMrModeGold_1", t_value)
            else:
                msg_reply = msg_manager.msg_format("strMrModeGold_2", t_value)
            game_work.upsert_info(msg_reply)
            comp.append(target)


class 勇者(ModeComp, BaseMode):
    name = "勇者"
    brief = (
        "〈赏金〉40"
        "\n〈血量〉每名玩家5hp."
        "\n〈道具池〉(上限12)"
        "\n{手铐,锯子,邀请函,花生,巧克力,香烟,红牛,放大镜,口红,扑克,转盘,牛奶,金币}"
        "\n〔机制〕"
        "\n1. 游戏开始时, 首发玩家抽取 1 个道具, 非首发玩家抽取 2 个道具."
        "\n2. 向自己开枪且为空包弹时抽取 2 个道具;"
        "\n3. 实弹有1/3的概率使伤害+1."
    )
    points = 40
    reply = (("strMrModeHero_1", "勇者模式 机制3的回复词", "伴隨七彩光芒，魔彈發射."),)

    class props(BaseMode.props):
        pool = (
            "手铐",
            "锯子",
            "邀请函",
            "花生",
            "巧克力",
            "香烟",
            "红牛",
            "放大镜",
            "口红",
            "扑克",
            "转盘",
            "牛奶",
            "金币",
        )
        limit = 12

    @classmethod
    def start(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        for pl in game_work.order:
            game_work.draw_prop(pl, 2 if pl != game_work.shooter else 1)

    @classmethod
    def join(cls, msg_manager, user_id):
        msg_manager.val["game"]["data"]["players"][user_id]["hp"] = 5

    # 开枪
    @classmethod
    def shoot(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        tmp = game_work.tmp
        if random.randint(1, 3) == 1:
            tmp["dmg"] += 1
            msg_reply = msg_manager.msg_format("strMrModeHero_1")
            game_work.upsert_info(msg_reply)
        target, is_attack_me = tmp["target"], tmp["is_attack_me"]
        if is_attack_me and not game_work.bullet:
            game_work.draw_prop(target, 2)


class 赌徒(ModeComp, BaseMode):
    name = "赌徒"
    brief = (
        "〈赏金〉40"
        "\n〈血量〉每名玩家5hp."
        "\n〈道具池〉(上限12)"
        "\n{手铐,锯子,邀请函,红牛,放大镜,口红,牛奶,金币}"
        "\n〔机制〕"
        "\n1. 游戏开始时, 所有玩家抽取 2 个道具;"
        "\n2. 向自己开枪且为空包弹时抽取 3 个道具;"
        "\n3. 每次开枪有1/3的概率反转子弹虚实;"
        "\n4. 实弹有1/3的概率使伤害+1;"
        "\n5. 不会正常显示弹药数量."
    )
    points = 40
    reply = (
        ("strMrModeGambler_1", "赌徒模式 机制3的回复词", "子彈擊穿突然出現的{poker}."),
        ("strMrModeGambler_2", "赌徒模式 机制4的回复词", "伴隨七彩光芒，魔彈發射."),
    )

    class props(BaseMode.props):
        pool = (
            "手铐",
            "锯子",
            "邀请函",
            "红牛",
            "放大镜",
            "口红",
            "牛奶",
            "金币",
            "烟花",
        )
        limit = 12

    class modify(BaseMode.modify):
        ammo_show = False

    @staticmethod
    def poker():
        if random.randint(1, 54) > 2:
            suits = ("方片♦️", "梅花♣️", "红桃♥️", "黑桃♠️")
            ranks = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
            return random.choice(suits) + random.choice(ranks)
        else:
            return random.choice(["JOKER", "joker"])

    @classmethod
    def start(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        for pl in game_work.order:
            game_work.draw_prop(pl, 2)

    @classmethod
    def join(cls, msg_manager, user_id):
        msg_manager.val["game"]["data"]["players"][user_id]["hp"] = 5

    # 开枪
    @classmethod
    def shoot(cls, msg_manager):
        game_work = GameWork.from_manager(msg_manager)
        data, tmp = game_work.data, game_work.tmp
        target, is_attack_me = tmp["target"], tmp["is_attack_me"]
        if is_attack_me and not game_work.bullet:
            game_work.draw_prop(target, 3)
        if random.randint(1, 3) == 1:
            if game_work.bullet:
                data["ammo_blank"] += 1
                data["ammo_live"] -= 1
            else:
                data["ammo_blank"] -= 1
                data["ammo_live"] += 1
            game_work.bullet = not game_work.bullet
            msg_reply = msg_manager.msg_format("strMrModeGambler_1", {"poker": cls.poker()})
            game_work.upsert_info(msg_reply)
        if data["bullet"] and random.randint(1, 3) == 1:
            tmp["dmg"] += 1
            msg_reply = msg_manager.msg_format("strMrModeGambler_2")
            game_work.upsert_info(msg_reply)


# class 大富翁(ModeComp, BaseMode):
#     name = "大富翁"
#     brief = ""
#     points = 0
#     reply: list = []

#     class props(BaseMode.props):
#         pool: list = ["金币"]
#         allow: list = ["和你爆了"]
#         ban: list = ["手铐", "口红", "止疼药"]
#         limit: int = 0

#     @classmethod
#     def join(cls, msg_manager, user_id):
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         players[user_id]["hp"] = 2

#     # 受伤
#     @classmethod
#     def damage(cls, msg_manager):
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         target, murderer = tmp["target"], tmp["murderer"]
#         if tmp["dmg"] <= 0:
#             if players[target]["hp"] > 2:
#                 tmp["dmg"] = 0
#             return
#         elif target != murderer:
#             RegGameWork.draw_prop(msg_manager, target, 1)
#             if players[target]["props"].count("金币") > 5:
#                 order[:] = [target]

#                 RegGameWork.is_over(msg_manager)

#     # 死亡
#     @classmethod
#     def dead(cls, msg_manager):
#         game, data, reply, tmp, modify, players, order, shooter, bullet = RegGameWork.get_index(msg_manager)
#         target, murderer = tmp["target"], tmp["murderer"]
#         if players[target]["surrender"]:
#             tmp["check_over"] = True
#             return
#         tmp["check_over"] = False
#         target, murderer = tmp["target"], tmp["murderer"]
#         pl_target, pl_murderer = players[target], players[murderer]
#         if target == murderer:
#             pass
#         else:
#             pass
#         order.append(target)
#         pl_target["hp"] = 2
#         pl_target["actions"] = 0
#         pl_target["kills"] = 0
#         pl_target["suicide"] = False
#         pl_murderer["kills"] = 0
