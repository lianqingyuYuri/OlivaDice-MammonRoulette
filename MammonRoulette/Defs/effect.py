# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Defs/effect.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from ..Core.base import BaseEffect
from ..Core.comp import EffectComp
from ..Core.work import GameWork


class 束缚(EffectComp, BaseEffect):
    name = "束缚"
    helpdoc = "被手铐囚禁的标识."

    @classmethod
    def apply(cls, msg_manager, target, stacks):
        game_work = GameWork.from_manager(msg_manager)
        effect_data = {"stacks": 1}
        game_work.create_effects_event(target, cls.name, effect_data)
        return True

    @classmethod
    def callback(cls, msg_manager, moment, target, effect_data):
        game_work = GameWork.from_manager(msg_manager)
        if moment != "switch" or target != game_work.shooter:
            return False
        return True


class 神经麻痹(EffectComp, BaseEffect):
    name = "神经麻痹"
    helpdoc = "回合结束时失去所有[神经麻痹], 并失去等值的HP."
    reply = (
        ("strMrEffectPain_1", "神经麻痹效果 层数增加", "{tGamblerName}沒感到疼痛[神经麻痹 {old_stacks}->{new_stacks}]."),
        ("strMrEffectPain_2", "神经麻痹效果 结算1", "{tGamblerName}的神經在悲鳴[hp {old_hp}->{new_hp}]……"),
        ("strMrEffectPain_3", "神经麻痹效果 结算2", "{tGamblerName}的藥效衰減, 不再止疼."),
    )

    @classmethod
    def apply(cls, msg_manager, target, stacks):
        game_work = GameWork.from_manager(msg_manager)
        pl_target = game_work.players[target]
        if cls.name not in pl_target["effects_event"]:
            expired = False if target == game_work.shooter else True
            pl_target["effects_event"][cls.name] = {
                "stacks": 0,
                "data": [],
                "expired": expired,
            }
        effect_data = pl_target["effects_event"][cls.name]
        if stacks > 0:
            effect_data["stacks"] += stacks
            effect_data["data"].append({"dmg": stacks, "source": game_work.tmp["source"]})
        return True

    @classmethod
    def callback(cls, msg_manager, moment, target, effect_data):
        game_work = GameWork.from_manager(msg_manager)
        pl_target = game_work.players[target]
        if moment == "damage" and target == game_work.tmp["target"] and game_work.tmp["dmg_type"] == "":
            old_stacks = effect_data["stacks"]
            dmg, game_work.tmp["dmg"] = game_work.tmp["dmg"], 0
            EffectComp.give(msg_manager, cls.name, target, dmg)
            msg_reply = msg_manager.msg_format(
                "strMrEffectPain_1",
                {"tGamblerName": game_work.get_name(target), "old_stacks": old_stacks, "new_stacks": old_stacks + dmg},
            )
            game_work.upsert_info(msg_reply)
            return False
        elif moment == "done" and target == game_work.shooter:
            effect_data = pl_target["effects_event"][cls.name]
            if not effect_data["expired"]:
                effect_data["expired"] = True
                return False
            game_work.tmp["dmg_type"] = cls.name
            game_work.tmp["is_check_over"] = False
            old_hp = pl_target["hp"]
            for data in effect_data["data"]:
                game_work.damage(target, data["dmg"], data["source"])
            if not game_work.try_over():
                if effect_data["stacks"] > 0:
                    msg_reply = msg_manager.msg_format(
                        "strMrEffectPain_2",
                        {"tGamblerName": pl_target["name"], "old_hp": old_hp, "new_hp": game_work.tmp["new_hp"]},
                    )
                else:
                    msg_reply = msg_manager.msg_format("strMrEffectPain_3", {"tGamblerName": pl_target["name"]})
                game_work.upsert_info(msg_reply)
            return True
