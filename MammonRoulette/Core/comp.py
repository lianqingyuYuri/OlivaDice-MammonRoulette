# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Core/comp.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

import MammonRoulette as MR

from .base import BaseMode, BaseProp, BaseEffect
from ..custom import (
    dictStrCustomNote,
    dictStrCustomTemplate,
    dictHelpDocTemplate,
    dictModeCustom,
    dictPropCustom,
    dictEffectCustom,
)

from AmorLib import Registerable


class ModeComp(Registerable):
    _register = {}

    @classmethod
    def init_after(cls):
        for mode_name, mode_cls in cls._register.items():
            mode_cls: BaseMode
            mode_cls.init()
            dictModeCustom["default"][mode_name] = {
                "points": mode_cls.points,
                "seats": {
                    "default": mode_cls.seats.default,
                    "max": mode_cls.seats.max,
                    "min": mode_cls.seats.min,
                },
                "props": {
                    "pool": mode_cls.props.pool,
                    "allowed": mode_cls.props.allowed,
                    "ban": mode_cls.props.ban,
                    "limit": mode_cls.props.limit,
                },
                "modify": {
                    "dmg": mode_cls.modify.dmg,
                    "ammo_visible": mode_cls.modify.ammo_visible,
                    "bullet_visible": mode_cls.modify.bullet_visible,
                },
            }
            dictHelpDocTemplate["default"].update(mode_cls.helpDocDefault)
            for field, (note, msg) in mode_cls.strCustomDefault.items():
                dictStrCustomNote[field] = note
                dictStrCustomTemplate["default"][field] = msg
        return

    @classmethod
    def trigger(cls, msg_manager, event):
        return getattr(cls.get(msg_manager.val["game"]["mode"]["name"]), event)(msg_manager)


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
    def use(cls, msg_manager, prop, user_id, target):
        if cls.get(prop).apply(msg_manager, target):
            MR.Core.work.GameWork.from_manager(msg_manager).remove_prop(user_id, prop)

    @classmethod
    def trigger(cls, msg_manager, prop, moment, prop_data):
        return cls.get(prop).callback(msg_manager, moment, prop_data)

    @classmethod
    def uninstall(cls, msg_manager, prop, prop_data):
        return cls.get(prop).unapply(msg_manager, prop_data)

    @classmethod
    def sustain(cls, msg_manager, prop, prop_data):
        return cls.get(prop).persist(msg_manager, prop_data)


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

    @classmethod
    def give(cls, msg_manager, effect, target, stacks: int = 1):
        return cls.get(effect).apply(msg_manager, target, stacks)

    @classmethod
    def trigger(cls, msg_manager, effect, moment, target, effect_data):
        return cls.get(effect).callback(msg_manager, moment, target, effect_data)

    @classmethod
    def uninstall(cls, msg_manager, effect):
        return cls.get(effect).unapply(msg_manager)


class BotComp(Registerable):
    _register = {}

    @classmethod
    def load_all(cls):
        for _name, bot_cls in cls._register.items():
            bot_cls.load()

    @classmethod
    def save_all(cls):
        for _name, bot_cls in cls._register.items():
            bot_cls.save()

    @classmethod
    def action(cls, msg_manager):
        game_work = MR.Core.work.GameWork.from_manager(msg_manager)
        if game_work.flag_over:
            return
        shooter = game_work.shooter
        bot_model = game_work.players[shooter].get("bot_model")

        state = game_work.get_bot_state(shooter)
        action = cls.get(bot_model).decide(state)

        if action.type == action.SHOOT_SELF:
            game_work.shoot(shooter)
        elif action.type == action.SHOOT_OTHER:
            target = game_work.get_target(action.target)
            if target:
                game_work.shoot(target)
        elif action.type == action.USE_PROP:
            target = game_work.get_target(action.target)
            if target and action.prop and action.prop in game_work.players[shooter].get("props", []):
                PropComp.use(msg_manager, action.prop, shooter, target)
        if game_work.flag_bot:
            cls.action(msg_manager)
        return
