# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Core/comp.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from AmorLib import Registerable

import MammonRoulette as MR

from ..custom import (
    dictEffectCustom,
    dictHelpDocTemplate,
    dictPropCustom,
    dictStrCustomNote,
    dictStrCustomTemplate,
)
from .base import BaseEffect, BaseProp


class PropComp(Registerable):
    _register = {}

    @classmethod
    def init_after(cls):
        for prop_name, prop_cls in cls._register.items():
            prop_cls: BaseProp
            prop_cls.init()
            dictPropCustom["default"][prop_name] = {}
            dictHelpDocTemplate["default"].update(prop_cls.helpDocDefault)
            for field, (note, msg) in prop_cls.strCustomDefault.items():
                dictStrCustomNote[field] = note
                dictStrCustomTemplate["default"][field] = msg
        return

    @classmethod
    def apply(cls, msg_event, prop, user_id, target):
        if cls.get(prop).apply(msg_event, target):
            MR.Core.work.GameWork.from_manager(msg_event).remove_prop(user_id, prop)


class EffectComp(Registerable):
    _register = {}

    @classmethod
    def init_after(cls):
        for effect_name, effect_cls in cls._register.items():
            effect_cls: BaseEffect
            effect_cls.init()
            dictEffectCustom["default"][effect_name] = {}
            dictHelpDocTemplate["default"].update(effect_cls.helpDocDefault)
            for field, (note, msg) in effect_cls.strCustomDefault.items():
                dictStrCustomNote[field] = note
                dictStrCustomTemplate["default"][field] = msg
        return


class BotComp(Registerable):
    _register = {}

    @classmethod
    def load_all(cls):
        for bot_cls in cls._register.values():
            bot_cls.load()

    @classmethod
    def save_all(cls):
        for bot_cls in cls._register.values():
            bot_cls.save()

    @classmethod
    def action(cls, msg_event):
        game_work = MR.Core.work.GameWork.from_manager(msg_event)
        bot_mark = msg_event.msg_format("strMrBotMark")
        while not game_work.flag_over and game_work.flag_bot:
            shooter = game_work.shooter
            bot_cls = cls.get(game_work.players[shooter]["bot_model"])
            bot_name = game_work.get_name(shooter)
            state = game_work.get_state()
            memory = {}
            while not game_work.flag_over and game_work.shooter == shooter:
                game_work.tmp.clear()
                action = bot_cls.decide(msg_event, state, memory)
                memory = action.memory
                target = game_work.get_target(action.target) if action.target else shooter

                if action.type == action.SHOOT_SELF:
                    game_work.upsert_info(msg_event.msg_format("strMrBotShootSelf", {"tBotMark": bot_mark, "tBotName": bot_name}))
                    game_work.shoot(shooter)
                elif action.type == action.SHOOT_OTHER:
                    game_work.upsert_info(
                        msg_event.msg_format(
                            "strMrBotShootOther",
                            {"tBotMark": bot_mark, "tBotName": bot_name, "tTargetName": game_work.get_name(target)},
                        )
                    )
                    game_work.shoot(target)
                elif action.type == action.USE_PROP:
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
                    PropComp.apply(msg_event, action.prop, shooter, target)
                else:
                    break
                state = game_work.get_state()
                for f, v in memory.items():
                    setattr(state, f, v)
        return
