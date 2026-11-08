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


# region bot


@dataclass
class PlayerView:
    index: int = 0
    name: str = ""
    hp: int = 0
    props: tuple = ()
    effects: tuple = ()
    actions: int = 0
    is_self: bool = False
    is_shooter: bool = False
    is_alive: bool = True


@dataclass
class BotGameState:
    my_hp: int = 0
    my_actions: int = 0
    my_props: tuple = ()
    my_effects: tuple = ()

    players: tuple = ()

    bullet: int = -1
    bullet_visible: bool = False

    ammo_live: int = -1
    ammo_blank: int = -1
    ammo_total: int = -1
    ammo_visible: bool = False

    mode_name: str = ""
    player_count: int = 0
    alive_count: int = 0

    def to_vector(self) -> tuple:
        vec = [
            self.my_hp,
            self.my_actions,
            self.bullet,
            int(self.bullet_visible),
            self.ammo_live,
            self.ammo_blank,
            self.ammo_total,
            int(self.ammo_visible),
            self.player_count,
            self.alive_count,
        ]
        for pl in self.players:
            vec.extend([pl.hp, int(pl.is_self), int(pl.is_shooter), int(pl.is_alive)])
        vec.append(len(self.my_props))
        for prop in self.my_props:
            vec.append(hash(prop) % 1000)
        return tuple(vec)


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
    def decide(cls, state: BotGameState) -> BotAction:
        raise NotImplementedError

    @classmethod
    def load(cls):
        pass

    @classmethod
    def save(cls):
        pass


# endregion
