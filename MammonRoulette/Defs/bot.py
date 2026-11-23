# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Defs/bot.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    Bot 定义 - 在此注册所有 Bot 子类
"""

from ..Core.base import BaseBot, BotAction, GameState, PlayerView
from ..Core.registry import botDef, propReg
from ..Core.work import GameWork


def prop_can_use(msg_event, prop_name, target: str | None = None):
    game_work = GameWork.from_manager(msg_event)
    if target is None:
        target = game_work.shooter
    target = game_work.get_target(target)
    return propReg.get(prop_name).can_use(msg_event, target)


@botDef()
class 达尔文(BaseBot):
    name = "达尔文"

    @classmethod
    def decide(cls, msg_event, state: GameState, memory):
        me: PlayerView = state.pl_self
        enemies = [pl for pl in state.players if not pl.is_self and not pl.is_dead]
        if not enemies:
            return BotAction.skip()
        pv_target = min(enemies, key=lambda p: p.hp)

        if "手铐" in me.props and prop_can_use(msg_event, "手铐", pv_target.id):
            return BotAction.use_prop("手铐", pv_target.id)
        for prop in ("红牛", "牛奶", "止疼药"):
            if prop in me.props and prop_can_use(msg_event, prop):
                return BotAction.use_prop(prop, me.id)

        if "口红" in me.props and prop_can_use(msg_event, "口红", pv_target.id):
            prop_enemies = [e for e in enemies if e.props]
            if prop_enemies:
                prop_enemy = min(prop_enemies, key=lambda p: p.hp)
                return BotAction.use_prop("口红", prop_enemy.id)
        if "烟花" in me.props and me.hp >= 2 and prop_can_use(msg_event, "烟花", pv_target.id):
            return BotAction.use_prop("烟花", me.id)

        if state.bullet_visible:  # 子弹可见
            if state.bullet == 1:
                if "锯子" in me.props and prop_can_use(msg_event, "锯子"):
                    return BotAction.use_prop("锯子", me.id, memory=memory)
            if state.bullet == 0:
                if "扑克" in me.props and prop_can_use(msg_event, "扑克"):
                    return BotAction.use_prop("扑克", me.id, memory={"bullet": 1, "bullet_visible": True})
                for prop in ("巧克力", "花生", "香烟", "转盘"):
                    if prop in me.props and prop_can_use(msg_event, prop):
                        return BotAction.use_prop(prop, me.id)
                return BotAction.shoot_self()
        else:  # 子弹不可见
            if "放大镜" in me.props and prop_can_use(msg_event, "放大镜"):
                return BotAction.use_prop("放大镜", me.id)
            if (
                "邀请函" in me.props and prop_can_use(msg_event, "邀请函") and len(me.props) + 2 <= state.props_limit
            ):  # 道具栏未满
                return BotAction.use_prop("邀请函", me.id)

        if len(me.props) + 2 >= state.props_limit:  # 道具栏快满
            for prop in ("巧克力", "花生", "香烟", "转盘"):
                if prop in me.props and prop_can_use(msg_event, prop):
                    return BotAction.use_prop(prop, me.id)

        return BotAction.shoot_other(pv_target.id)
