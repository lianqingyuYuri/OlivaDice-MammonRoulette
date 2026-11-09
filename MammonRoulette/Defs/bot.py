# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Defs/bot.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    Bot 定义 - 在此注册所有 Bot 子类
"""

from ..Core.base import BaseBot, PlayerView, BotGameState, BotAction
from ..Core.comp import BotComp
from ..Core.work import GameWork


class 达尔文(BotComp, BaseBot):
    name = "达尔文"

    @classmethod
    def decide(cls, state):
        me = state.pl_self
        enemies = [pl for pl in state.players if not pl.is_self and not pl.is_dead]
        if not enemies:
            return BotAction.skip()
        target = min(enemies, key=lambda p: p.hp)

        if "手铐" in me.props:
            return BotAction.use_prop("手铐", target.index)
        if "红牛" in me.props:
            return BotAction.use_prop("红牛")
        if "牛奶" in me.props:
            return BotAction.use_prop("牛奶")
        if "止疼药" in me.props:
            return BotAction.use_prop("止疼药")

        if "口红" in me.props:
            prop_enemies = [e for e in enemies if e.props]
            if prop_enemies:
                prop_enemy = min(prop_enemies, key=lambda p: p.hp)
                return BotAction.use_prop("口红", str(prop_enemy.index))
        if "放大镜" in me.props and state.bullet == -1:
            return BotAction.use_prop("放大镜")
        if "烟花" in me.props and target.hp < 2 and me.hp >= 2:
            return BotAction.use_prop("烟花")

        if state.bullet_visible:
            if state.bullet == 1:
                if "锯子" in me.props:
                    return BotAction.use_prop("锯子")
            if state.bullet == 0:
                if "扑克" in me.props:
                    return BotAction.use_prop("扑克", memory={"bullet": 1, "bullet_visible": True})
                for prop in ("巧克力", "花生", "香烟", "转盘"):
                    if prop in me.props:
                        return BotAction.use_prop(prop)
                return BotAction.shoot_self()

        return BotAction.shoot_other(str(target.index))
