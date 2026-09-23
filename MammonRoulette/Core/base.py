class BaseMode:
    name: str = ""
    helpdoc: str = ""
    points: int = 0
    reply: tuple = ()

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
    def end_round(cls, msg_manager):
        pass

    # 换人
    @classmethod
    def switch(cls, msg_manager):
        pass


class BaseProp:
    name: str = ""
    helpdoc: str = ""
    allow_flag: bool = True
    reply: tuple = ()

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
    helpdoc: str = ""
    reply: tuple = ()

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
