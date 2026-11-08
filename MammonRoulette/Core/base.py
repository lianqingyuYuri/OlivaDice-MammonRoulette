# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Core/base.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from dataclasses import dataclass


class BaseMode:
    name: str = ""
    strCustomDefault: dict = {}
    helpDocDefault: dict = {}
    points: int = 0

    class seats:
        default: int = 2
        max: int = 8
        min: int = 2

    class props:
        pool: tuple = ()
        allow: tuple = ()
        ban: tuple = ()
        limit: int = 0

    class modify:
        dmg: int = 1
        flag_ammo_show: bool = True
        flag_bullet_show: bool = False

    @classmethod
    def init(cls):
        pass

    @classmethod
    def start(cls, msg_manager):
        pass

    @classmethod
    def join(cls, msg_manager, user_id):
        pass

    @classmethod
    def try_over(cls, msg_manager) -> bool:
        return False

    # 装弹
    @classmethod
    def reload(cls, msg_manager):
        pass

    # 开枪
    @classmethod
    def shoot(cls, msg_manager):
        pass

    # 受伤
    @classmethod
    def damage(cls, msg_manager):
        pass

    # 死亡
    @classmethod
    def dead(cls, msg_manager):
        pass

    # 回合结束
    @classmethod
    def done(cls, msg_manager):
        pass

    # 换人
    @classmethod
    def switch(cls, msg_manager):
        pass


class BaseProp:
    name: str = ""
    strCustomDefault: dict = {}
    helpDocDefault: dict = {}
    allow_flag: bool = True

    @classmethod
    def init(cls):
        pass

    # 使用
    @classmethod
    def apply(cls, msg_manager, target) -> bool | None:
        return False

    # 回调
    @classmethod
    def callback(cls, msg_manager, moment, prop_data=None) -> bool | None:
        pass

    # 卸载
    @classmethod
    def unapply(cls, msg_manager, prop_data=None) -> bool | None:
        pass

    # 持久化
    @classmethod
    def persist(cls, msg_manager, prop_data=None) -> bool | None:
        pass


class BaseEffect:
    name: str = ""
    strCustomDefault: dict = {}
    helpDocDefault: dict = {}

    @classmethod
    def init(cls):
        pass

    # 应用
    @classmethod
    def apply(cls, msg_manager, target, stacks) -> bool | None:
        return False

    # 回调
    @classmethod
    def callback(cls, msg_manager, moment, target, effect_data) -> bool | None:
        pass

    # 卸载
    @classmethod
    def unapply(cls, msg_manager) -> bool | None:
        pass


@dataclass
class BotAction:
    type: str = ""
    target: str = ""
    prop: str = ""

    SHOOT_SELF = "shoot_self"
    SHOOT_OTHER = "shoot_other"
    USE_PROP = "use_prop"
    SKIP = "skip"

    @classmethod
    def shoot_self(cls):
        return cls(type=cls.SHOOT_SELF)

    @classmethod
    def shoot_other(cls, target: str):
        return cls(type=cls.SHOOT_OTHER, target=target)

    @classmethod
    def use_prop(cls, prop: str, target: str = ""):
        return cls(type=cls.USE_PROP, prop=prop, target=target)

    @classmethod
    def skip(cls):
        return cls(type=cls.SKIP)


class BaseBot:
    name: str = ""

    @classmethod
    def decide(cls, game_work) -> BotAction:
        raise NotImplementedError

    @classmethod
    def load(cls):
        pass

    @classmethod
    def save(cls):
        pass
