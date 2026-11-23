# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Core/base.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from dataclasses import dataclass, field
from enum import Enum


class Moment(str, Enum):
    RELOAD = "reload"
    SHOOT = "shoot"
    DAMAGE = "damage"
    DEAD = "dead"
    DONE = "done"
    SWITCH = "switch"


class BaseMode:
    name: str = ""
    points: int = 0

    class seats:
        default: int = 2
        max: int = 8
        min: int = 2

    class props:
        pool: tuple = ()
        allowed: tuple = ()
        banned: tuple = ()
        limit: int = 0

    class modify:
        dmg: int = 1
        ammo_visible: bool = True
        bullet_visible: bool = False

    @classmethod
    def init(cls):
        pass

    @classmethod
    def start(cls, msg_event):
        pass

    @classmethod
    def join(cls, msg_event, user_id):
        pass

    @classmethod
    def try_over(cls, msg_event) -> bool:
        return False

    # 装弹
    @classmethod
    def reload(cls, msg_event):
        pass

    # 开枪
    @classmethod
    def shoot(cls, msg_event):
        pass

    # 受伤
    @classmethod
    def damage(cls, msg_event):
        pass

    # 死亡
    @classmethod
    def dead(cls, msg_event):
        pass

    # 回合结束
    @classmethod
    def done(cls, msg_event):
        pass

    # 换人
    @classmethod
    def switch(cls, msg_event):
        pass


class BaseProp:
    name: str = ""
    strCustomDefault: dict = field(default_factory=dict)
    helpDocDefault: dict = field(default_factory=dict)
    allowed: bool = True

    @classmethod
    def init(cls):
        pass

    @classmethod
    def can_use(cls, msg_event, target) -> bool:
        return True

    # 使用
    @classmethod
    def apply(cls, msg_event, target) -> bool | None:
        return False

    # 回调
    @classmethod
    def on_moment(cls, msg_event, moment, prop_data=None):
        pass

    # 卸载
    @classmethod
    def on_unregister(cls, msg_event, prop_data=None):
        pass

    # 持久化
    @classmethod
    def sustain(cls, msg_event, prop_data=None):
        pass


class BaseEffect:
    name: str = ""
    strCustomDefault: dict = field(default_factory=dict)
    helpDocDefault: dict = field(default_factory=dict)

    @classmethod
    def init(cls):
        pass

    # 应用
    @classmethod
    def apply(cls, msg_event, target, stacks):
        return False

    # 回调
    @classmethod
    def on_moment(cls, msg_event, moment, target, effect_data):
        pass

    # 卸载
    @classmethod
    def on_unregister(cls, msg_event):
        pass


# region bot
@dataclass
class PlayerView:
    id: str = ""
    name: str = ""
    hp: int = 0
    actions: int = 0

    props: tuple = ()
    effects: tuple = ()

    is_shooter: bool = False
    is_dead: bool = False


@dataclass
class GameState:
    pl_self: PlayerView = field(default_factory=PlayerView)

    # 模式参数
    mode_name: str = ""
    props_pool: tuple = ()
    props_allowed: tuple = ()
    props_banned: tuple = ()
    props_limit: int = 0

    players: tuple = ()
    props_event: tuple = ()

    # 状态参数
    shooter: str = ""
    order: tuple = ()
    player_count: int = 0
    alive_count: int = 0

    ammo_live: int = -1
    ammo_blank: int = -1
    ammo_total: int = -1
    ammo_visible: bool = False
    bullet: int = -1
    bullet_visible: bool = True
    dmg: int = 1

    def to_vector(self) -> tuple:
        vec = [
            self.dmg,
            self.bullet,
            int(self.bullet_visible),
            self.ammo_live,
            self.ammo_blank,
            self.ammo_total,
            int(self.ammo_visible),
            self.player_count,
            self.alive_count,
            hash(self.mode_name) % 1000,
        ]
        for pl in self.players:
            vec.extend(
                [
                    pl.hp,
                    pl.actions,
                    len(pl.props),
                    len(pl.effects),
                    int(pl.is_self),
                    int(pl.is_shooter),
                    int(pl.is_dead),
                ]
            )
            for prop in pl.props:
                vec.append(hash(prop) % 1000)
            for effect in pl.effects:
                vec.extend([hash(effect[0]) % 1000, effect[1]])
        for prop in self.props_event:
            vec.extend([hash(prop.get("name", "")) % 1000, prop.get("stacks", 0), prop.get("user_id", "")])
        return tuple(vec)


@dataclass
class BotAction:
    type: str = ""
    target: str = ""
    prop: str = ""
    memory: dict = field(default_factory=dict)

    SHOOT_SELF = "shoot_self"
    SHOOT_OTHER = "shoot_other"
    USE_PROP = "use_prop"
    SKIP = "skip"

    @classmethod
    def shoot_self(cls, memory: dict | None = None):
        return cls(type=cls.SHOOT_SELF, memory=memory or {})

    @classmethod
    def shoot_other(cls, target: str | int = "", memory: dict | None = None):
        return cls(type=cls.SHOOT_OTHER, target=str(target), memory=memory or {})

    @classmethod
    def use_prop(cls, prop: str, target: str | int = "", memory: dict | None = None):
        return cls(type=cls.USE_PROP, prop=prop, target=str(target), memory=memory or {})

    @classmethod
    def skip(cls, memory: dict | None = None):
        return cls(type=cls.SKIP, memory=memory or {})


class BaseBot:
    name: str = ""
    strCustomDefault: dict = field(default_factory=dict)
    helpDocDefault: dict = field(default_factory=dict)
    allowed: bool = True
    modes_allowed: tuple = ()

    @classmethod
    def decide(cls, msg_event, state: GameState, memory: dict) -> BotAction:
        raise NotImplementedError

    @classmethod
    def load(cls):
        pass

    @classmethod
    def save(cls):
        pass


# endregion
