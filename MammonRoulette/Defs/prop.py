# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/Defs/prop.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

import random
import string

from ..main import commands
from ..msgCustom import dictHelpDoc, dictModeCustom
from ..Core.base import BaseProp
from ..Core.comp import ModeComp, PropComp, EffectComp
from ..Core.work import GameWork


# region 道具
class 手铐(PropComp, BaseProp):
    name = "手铐"
    helpdoc = "不能将枪手选为目标. 束缚目标行动 1 回合, 且在目标恢复行动前无法将其再次选为手铐目标."
    reply = (
        ("strMrPropHandcuffs_1", "手铐道具 使用成功", "{tGamblerName}被銬住了{limb}."),
        ("strMrPropHandcuffs_2", "手铐道具 使用失败", "{tGamblerName}已經被銬住了."),
        ("strMrPropHandcuffsLimb", "手铐道具 随机描述", "双手|双手|双手|双腿"),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        # 默认目标为下一个玩家
        if target == game_work.shooter:
            target = game_work.order[(game_work.order.index(game_work.shooter) + 1) % len(game_work.order)]
        pl_target = game_work.players[target]
        if not game_work.get_effect_data(target, "束缚"):
            pl_target["actions"] -= 1
            msg_reply = msg_manager.msg_format(
                "strMrPropHandcuffs_1",
                {
                    "tGamblerName": pl_target["name"],
                    "limb": msg_manager.msg_format("strMrPropHandcuffsLimb", flagSplit=True),
                },
            )
            game_work.upsert_info(msg_reply)
            EffectComp.give(msg_manager, "束缚", target)
            return True
        msg_reply = msg_manager.msg_format("strMrPropHandcuffs_2", {"tGamblerName": pl_target["name"]})
        game_work.upsert_info(msg_reply)
        return False


class 锯子(PropComp, BaseProp):
    name = "锯子"
    helpdoc = "每次开枪前只能使用 1 次. 下一发子弹若为实弹则伤害 +1."
    reply = (
        ("strMrPropSaw_1", "锯子道具 使用成功", "槍管被鋸斷."),
        ("strMrPropSaw_2", "锯子道具 使用失败", "槍管早已被鋸斷."),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        if not game_work.get_prop_data(prop_name=cls.name):
            msg_reply = msg_manager.msg_format("strMrPropSaw_1")
            game_work.upsert_info(msg_reply)
            prop_data = {"name": cls.name}
            game_work.create_props_event(prop_data)
            return True
        msg_reply = msg_manager.msg_format("strMrPropSaw_2")
        game_work.upsert_info(msg_reply)
        return False

    @classmethod
    def callback(cls, msg_manager, moment, prop_data):
        if moment != "shoot":
            return False
        game_work = GameWork.from_manager(msg_manager)
        game_work.tmp["dmg"] += 1
        return True


class 邀请函(PropComp, BaseProp):
    name = "邀请函"
    helpdoc = "在特定道具池中, 使目标抽取 2 个道具, 并结束枪手回合."
    reply = (
        ("strMrPropInvite_1", "邀请函道具 对自己使用", "{tGamblerName}將邀請函撕碎."),
        ("strMrPropInvite_2", "邀请函道具 对目标使用", "{tGamblerName}邀請{tTargetName}參加宴會."),
    )
    pool = ("手铐", "锯子", "红牛", "放大镜", "口红", "牛奶", "止疼药")

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        name = game_work.get_name()
        if target == game_work.shooter:
            msg_reply = msg_manager.msg_format("strMrPropInvite_1", {"tGamblerName": name})
        else:
            msg_reply = msg_manager.msg_format(
                "strMrPropInvite_2",
                {"tGamblerName": name, "tTargetName": game_work.get_name(target)},
            )
        game_work.upsert_info(msg_reply)
        game_work.draw_prop(target, 2, cls.pool)
        game_work.tmp["consume_action"] = 1
        game_work.done()
        return True


class 花生(PropComp, BaseProp):
    name = "花生"
    helpdoc = "装填 1 发空弹, 然后重新上膛."
    reply = (("strMrPropPeanut_1", "花生道具 使用成功", "{tGamblerName}花生被塞進彈倉."),)

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        msg_reply = msg_manager.msg_format("strMrPropPeanut_1", {"tGamblerName": game_work.get_name()})
        game_work.upsert_info(msg_reply)
        game_work.ammo_blank += 1
        game_work.chamber()
        return True


class 巧克力(PropComp, BaseProp):
    name = "巧克力"
    helpdoc = "装填 1 发实弹, 然后重新上膛."
    reply = (
        ("strMrPropChocolate_1", "巧克力道具 使用成功", "{heart}巧克力被塞進彈倉."),
        ("strMrPropChocolateHeart", "巧克力道具 随机描述", "酒心|果仁|果醬|奶油|焦糖|咖啡|抹茶|香草|芝士|辣味|慕斯|奶油"),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        msg_reply = msg_manager.msg_format(
            "strMrPropChocolate_1",
            {"heart": msg_manager.msg_format("strMrPropChocolateHeart", flagSplit=True)},
        )
        game_work.upsert_info(msg_reply)
        game_work.ammo_live += 1
        game_work.chamber()
        return True


class 香烟(PropComp, BaseProp):
    name = "香烟"
    helpdoc = "取出 1 发空弹, 然后重新上膛. 若弹仓内只有实弹, 则取出 1 发实弹."
    reply = (("strMrPropSmoke_1", "香烟道具 使用成功", "{tGamblerName}扔掉香煙, 取出一發{tNowBulletType}."),)

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        if game_work.ammo_blank > 0:
            game_work.ammo_blank -= 1
            bullet = False
        else:
            game_work.ammo_live -= 1
            bullet = True
        t_value = {
            "tGamblerName": game_work.get_name(),
            "tNowBulletType": msg_manager.msg_format("strMrAmmoLive" if bullet else "strMrAmmoBlank"),
        }
        msg_reply = msg_manager.msg_format("strMrPropSmoke_1", t_value)
        game_work.upsert_info(msg_reply)
        game_work.chamber()
        return True


class 红牛(PropComp, BaseProp):
    name = "红牛"
    helpdoc = "使目标HP+1."
    reply = (
        (
            "strMrPropRedCow_1",
            "红牛道具 对自己使用",
            "{tGamblerName}將混著{ingredients}的紅牛將其一飲而盡[hp {tHpOld}->{tHpNew}].",
        ),
        (
            "strMrPropRedCow_2",
            "红牛道具 对他人使用",
            "{tGamblerName}將混著{ingredients}的紅牛喂給{tTargetName}[hp {tHpOld}->{tHpNew}].",
        ),
        ("strMrPropRedCowIngredients", "红牛道具 随机描述", "胰岛素|白開水|辣椒粉|薯片|益達|紅牛?"),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        game_work.tmp["dmg_type"] = cls.name
        game_work.damage(target, -1, game_work.shooter)
        name = game_work.get_name()
        if target == game_work.shooter:
            msg_reply = msg_manager.msg_format(
                "strMrPropRedCow_1",
                {
                    "tGamblerName": name,
                    "ingredients": msg_manager.msg_format("strMrPropRedCowIngredients", flagSplit=True),
                    "tHpOld": game_work.tmp["old_hp"],
                    "tHpNew": game_work.tmp["new_hp"],
                },
            )
        else:
            msg_reply = msg_manager.msg_format(
                "strMrPropRedCow_2",
                {
                    "tGamblerName": name,
                    "ingredients": msg_manager.msg_format("strMrPropRedCowIngredients", flagSplit=True),
                    "tTargetName": game_work.get_name(target),
                    "tHpOld": game_work.tmp["old_hp"],
                    "tHpNew": game_work.tmp["new_hp"],
                },
            )
        game_work.upsert_info(msg_reply)
        return True


class 放大镜(PropComp, BaseProp):
    name = "放大镜"
    helpdoc = "每次开枪前只能使用 1 次. 在开枪前持续显示下一发子弹的虚实."
    reply = (
        ("strMrPropMagnifier_1", "放大镜道具 使用成功", "{tGamblerName}砸碎放大鏡, 發現槍膛裏是{tNowBulletType}."),
        ("strMrPropMagnifier_2", "放大镜道具 使用失败", "已用放大镜, 开枪前可查看子弹虚实."),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        if not game_work.get_prop_data(prop_name=cls.name):
            t_value = {
                "tGamblerName": game_work.get_name(),
                "tNowBulletType": msg_manager.msg_format("strMrAmmoLive" if game_work.bullet else "strMrAmmoBlank"),
            }
            msg_reply = msg_manager.msg_format("strMrPropMagnifier_1", t_value)
            game_work.upsert_info(msg_reply)
            prop_data = {"name": cls.name}
            cls.persist(msg_manager, prop_data)
            game_work.create_props_event(prop_data)
            return True
        msg_reply = msg_manager.msg_format("strMrPropMagnifier_2")
        game_work.upsert_info(msg_reply)
        return False

    @classmethod
    def callback(cls, msg_manager, moment, prop_data):
        if moment == "shoot":
            return True
        return False

    @classmethod
    def unapply(cls, msg_manager, prop_data):
        game_work = GameWork.from_manager(msg_manager)
        bot_hash = msg_manager.bot_hash
        modf_cfg = dictModeCustom[bot_hash][game_work.game["mode"]["name"]]
        game_work.flag_ammo_show = modf_cfg["modify"]["flag_ammo_show"]
        game_work.flag_bullet_show = modf_cfg["modify"]["flag_bullet_show"]
        return

    @classmethod
    def persist(cls, msg_manager, prop_data):
        game_work = GameWork.from_manager(msg_manager)
        game_work.flag_ammo_show = True
        game_work.flag_bullet_show = True
        return True


class 口红(PropComp, BaseProp):
    name = "口红"
    helpdoc = "夺取目标口红和金币以外的 1 个道具, 或重新抽取 1 个道具."
    reply = (
        ("strMrPropLipstick_1", "口红道具 对自己使用或目标无道具", "{tGamblerName}{usage}{color}的口紅, 神明贈予{tPropName}."),
        ("strMrPropLipstick_2", "口红道具 对目标使用", "{tGamblerName}給{usage}{color}的口紅, {tTargetName}以{tPropName}回贈."),
        ("strMrPropLipstickUsage", "口红道具 随机描述", "塗上|塗上|吃下"),
        (
            "strMrPropLipstickColor",
            "口红道具 随机色号",
            "複古正紅|牛血色|姨妈紅|梅子紅|磚紅色|楓葉紅|車厘子紅|酒紅色|山楂紅|朱砂紅|元氣橙色|珊瑚色|西柚色|南瓜色|胡蘿蔔色|髒橘色|赤陶色|焦糖色|芒果色|柿子色|淺粉色|桃粉色|玫瑰色|煙熏玫瑰|幹枯玫瑰|豆沙紅|幹枯玫瑰|豆沙粉|薔薇粉|奶茶玫瑰|蜜桃缤纷的黑|顔色正在變幻?",
        ),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        props_list = [prop for prop in game_work.players[target]["props"] if prop not in ("口红", "金币")]
        name = game_work.get_name()
        usage = msg_manager.msg_format("strMrPropLipstickUsage", flagSplit=True)
        color = msg_manager.msg_format("strMrPropLipstickColor", flagSplit=True)
        if target == game_work.shooter or not props_list:
            prop = random.choice(game_work.props_pool)
            msg_reply = msg_manager.msg_format(
                "strMrPropLipstick_1",
                {"tGamblerName": name, "usage": usage, "color": color, "tPropName": prop},
            )
            game_work.upsert_info(msg_reply)
        else:
            prop = random.choice(props_list)
            target_name = game_work.get_name(target)
            msg_reply = msg_manager.msg_format(
                "strMrPropLipstick_2",
                {"tGamblerName": name, "usage": usage, "color": color, "tTargetName": target_name, "tPropName": prop},
            )
            game_work.upsert_info(msg_reply)
            game_work.remove_prop(target, prop)
        game_work.remove_prop(game_work.shooter, cls.name)
        game_work.get_prop(game_work.shooter, prop)
        return False


class 扑克(PropComp, BaseProp):
    name = "扑克"
    helpdoc = "反转子弹虚实, 并在效果期间隐藏弹仓."
    reply = (
        ("strMrPropPoker_1", "扑克道具 使用成功", "{tGamblerName}從牌堆抽到[{poker}], 命運已然改變."),
        ("strMrPropPoker_2", "扑克道具 失效", "迷霧被驅散了."),
        ("strMrPropPokerSuits", "扑克道具 花色", "方片♦️|梅花♣️|紅桃♥️|黑桃♠️"),
        ("strMrPropPokerRanks", "扑克道具 点数", "A|2|3|4|5|6|7|8|9|10|J|Q|K"),
        ("strMrPropPokerJoker", "扑克道具 大小王", "JOKER|joker"),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        if random.randint(1, 54) > 2:
            poker = msg_manager.msg_format("strMrPropPokerSuits", flagSplit=True) + msg_manager.msg_format(
                "strMrPropPokerRanks", flagSplit=True
            )
        else:
            poker = msg_manager.msg_format("strMrPropPokerJoker", flagSplit=True)
        msg_reply = msg_manager.msg_format(
            "strMrPropPoker_1",
            {
                "tGamblerName": game_work.get_name(),
                "poker": poker,
            },
        )
        game_work.upsert_info(msg_reply)
        prop_data = {"name": cls.name}
        if not game_work.get_prop_data(prop_name=cls.name):
            game_work.create_props_event(prop_data)
        if game_work.bullet:
            game_work.ammo_blank += 1
            game_work.ammo_live -= 1
        else:
            game_work.ammo_blank -= 1
            game_work.ammo_live += 1
        game_work.bullet = not game_work.bullet
        cls.persist(msg_manager, prop_data)
        return True

    @classmethod
    def callback(cls, msg_manager, moment, prop_data):
        if moment in ["shoot", "reload"]:
            return True
        return False

    @classmethod
    def unapply(cls, msg_manager, prop_data):
        game_work = GameWork.from_manager(msg_manager)
        bot_hash = msg_manager.bot_hash
        modf_cfg = dictModeCustom[bot_hash][game_work.game["mode"]["name"]]
        game_work.flag_ammo_show = modf_cfg["modify"]["flag_ammo_show"]
        game_work.flag_bullet_show = modf_cfg["modify"]["flag_bullet_show"]
        msg_reply = msg_manager.msg_format("strMrPropPoker_2")
        game_work.upsert_info(msg_reply)
        return

    @classmethod
    def persist(cls, msg_manager, prop_data):
        game_work = GameWork.from_manager(msg_manager)
        game_work.flag_ammo_show = False
        game_work.flag_bullet_show = False
        return


class 转盘(PropComp, BaseProp):
    name = "转盘"
    helpdoc = "以特殊比例重新装填弹仓, 并重置道具特效."
    reply = (("strMrPropRoulette_1", "转盘道具 使用成功", "鏽迹斑斑的轉盤開始變換……現在是世界線[{garbled}]."),)

    clear_prop = ["扑克"]

    @staticmethod
    def garbled():
        return "".join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(8))

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        msg_reply = msg_manager.msg_format(
            "strMrPropRoulette_1",
            {"garbled": cls.garbled()},
        )
        game_work.upsert_info(msg_reply)
        ammo = random.randint(1, 6)
        ammo_blank = ammo - random.randint(1, ammo)
        ammo_live = ammo - ammo_blank
        game_work.ammo_live, game_work.ammo_blank = ammo_live, ammo_blank
        game_work.chamber()
        for clear_prop in cls.clear_prop:
            prop_data = game_work.get_prop_data(prop_name=clear_prop)
            if prop_data:
                game_work.remove_props_event(prop_data[0]["id"])
        game_work.reply["note"]["flag_ammo"] = True
        return True


class 牛奶(PropComp, BaseProp):
    name = "牛奶"
    helpdoc = "在特定道具池中, 使目标抽取 2 个道具, 其余赌徒抽取 1 个道具."
    reply = (
        ("strMrPropMilk_1", "牛奶道具 对自己使用", "{tGamblerName}飲下{milk}, 在暈眩中神明降下賜福.."),
        ("strMrPropMilk_2", "牛奶道具 对目标使用", "{tGamblerName}讓{tTargetName}飲下{milk}, 在暈眩中神明降下賜福.."),
        (
            "strMrPropMilkType",
            "牛奶道具 随机描述",
            "生鮮牛乳|酸奶|純牛奶|調味奶|炼乳|奶昔|奶酪|複原乳|濃縮牛乳|變質牛乳|冷凍牛乳",
        ),
    )
    pool = ("手铐", "锯子", "邀请函", "花生", "巧克力", "香烟", "红牛", "放大镜", "口红", "扑克", "转盘")

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        name = game_work.get_name()
        milk = msg_manager.msg_format("strMrPropMilkType", flagSplit=True)
        if target == game_work.shooter:
            msg_reply = msg_manager.msg_format("strMrPropMilk_1", {"tGamblerName": name, "milk": milk})
        else:
            msg_reply = msg_manager.msg_format(
                "strMrPropMilk_2", {"tGamblerName": name, "tTargetName": game_work.get_name(target), "milk": milk}
            )
        game_work.upsert_info(msg_reply)
        game_work.draw_prop(target, 2, cls.pool)
        for pl in game_work.order:
            if pl != target:
                game_work.draw_prop(pl, 1, cls.pool)
        return True


class 金币(PropComp, BaseProp):
    name = "金币"
    helpdoc = "兑换任意 1 个未被ban的道具, 部分道具兑换后将直接使用. 增加指令: 购买(道具名)."
    direct_use = ["锯子", "花生", "巧克力", "香烟", "放大镜", "扑克", "转盘", "牛奶"]

    reply = (
        ("strMrPropGold_1", "金币道具 使用成功", "{tGamblerName}向自動販賣機投入一枚{quality}的金幣, 自動販賣機吐出{tPropName}."),
        (
            "strMrPropGold_2",
            "金币道具 使用成功",
            "{tGamblerName}向自動販賣機投入一枚{quality}的金幣, 結果沒有任何反應, {tGamblerName}將其砸爛，取出{tPropName}.",
        ),
        ("strMrPropGold_3", "金币道具 禁售提示", "{tPropName}被禁售了."),
        ("strMrPropGoldQuality", "金币道具 随机描述", "嶄新|啞暗|磨損|變形|鏽蝕|斑駁|鏤空|黏膩|沾血"),
    )

    @classmethod
    def init(cls):
        prop_list = (prop for prop in PropComp.list() if prop != cls.name)
        dictHelpDoc["恶赌 命令"] += "\n[购买,購買](道具名) //使用金币兑换道具."

        @commands.route("play", f"^(?:购买|購買) *({'|'.join(prop_list)})$")
        def purchase(plugin_event, Proc, msg_manager, groups):
            user_id = msg_manager.user_id
            game_work = GameWork.from_manager(msg_manager)
            if user_id != game_work.shooter:
                msg_reply = msg_manager.msg_format(
                    "strMrGamblerTurn",
                    {"tGamblerName": game_work.get_name()},
                )
                plugin_event.reply(msg_reply)
                return
            if not game_work.remove_prop(user_id, cls.name):
                msg_reply = msg_manager.msg_format("strMrGamblerNoProp", {"tPropName": cls.name})
                plugin_event.reply(msg_reply)
                return
            prop = groups[0]
            actual_prop = game_work.get_prop(user_id, prop)
            if prop != actual_prop:
                game_work.remove_prop(user_id, actual_prop)
                game_work.get_prop(user_id, cls.name)
                game_work.upsert_info(msg_manager.msg_format("strMrPropGold_3", {"tPropName": prop}))
                msg_reply = game_work.format_reply()
                plugin_event.reply(msg_reply)
                return
            name = game_work.get_name(user_id)
            t_value = {
                "tGamblerName": name,
                "tPropName": prop,
                "quality": msg_manager.msg_format("strMrPropGoldQuality", flagSplit=True),
            }
            if random.randint(1, 4) == 1:
                msg_reply = msg_manager.msg_format("strMrPropGold_1", t_value)
            else:
                msg_reply = msg_manager.msg_format("strMrPropGold_2", t_value)
            game_work.upsert_info(msg_reply)
            if prop in cls.direct_use:
                PropComp.use(msg_manager, prop, user_id, user_id)
            msg_reply = game_work.format_reply()
            plugin_event.reply(msg_reply)
            return


class 止疼药(PropComp, BaseProp):
    name = "止疼药"
    helpdoc = "使目标在其回合结束前受到的伤害转变为等值的神经麻痹. 对自身使用时, 效果延长到下回合结束."
    reply = (
        ("strMrPropPain_1", "止疼药道具 对自己使用", "{tGamblerName}服用止疼药."),
        ("strMrPropPain_2", "止疼药道具 对目标使用", "{tGamblerName}喂{tTargetName}服用止疼药."),
        ("strMrPropPain_3", "止疼药道具 使用失败", "{tGamblerName}已服用止疼药."),
    )

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        if game_work.get_effect_data(target, "神经麻痹"):
            msg_reply = msg_manager.msg_format("strMrPropPain_3", {"tGamblerName": game_work.get_name(target)})
            game_work.upsert_info(msg_reply)
            return False
        if target == game_work.shooter:
            msg_reply = msg_manager.msg_format("strMrPropPain_1", {"tGamblerName": game_work.get_name(target)})
        else:
            msg_reply = msg_manager.msg_format(
                "strMrPropPain_2",
                {
                    "tGamblerName": game_work.get_name(),
                    "tTargetName": game_work.get_name(target),
                },
            )
        game_work.upsert_info(msg_reply)
        EffectComp.give(msg_manager, "神经麻痹", target, 0)
        return True


class 烟花(PropComp, BaseProp):
    name = "烟花"
    helpdoc = "所有赌徒各有1/2的概率HP-1. 每杀死一名赌徒, 重新生效一次, 且概率提高至2/3. 每生效一次, 所有赌徒抽取 1 个道具."
    reply = (("strMrPropFirework_1", "烟花道具 使用成功", "{tGamblerName}燃放煙花, 天空變得五彩斑斕."),)

    @classmethod
    def apply(cls, msg_manager, target):
        game_work = GameWork.from_manager(msg_manager)
        msg_reply = msg_manager.msg_format("strMrPropFirework_1", {"tGamblerName": game_work.get_name(target)})
        game_work.upsert_info(msg_reply)
        prop_data = {"name": cls.name, "data": {"reactivation": 0, "draws": 1}}
        game_work.create_props_event(prop_data)
        game_work.tmp["check_over"] = False
        order_before = game_work.order.copy()
        for pl in order_before:
            c_hp = game_work.players[pl]["hp"]
            game_work.tmp[f"{pl}_old_hp"] = c_hp
            game_work.tmp[f"{pl}_new_hp"] = c_hp
            if random.randint(1, 2) == 1:
                game_work.damage(pl, 1, game_work.shooter)
                game_work.tmp[f"{pl}_new_hp"] = game_work.tmp["new_hp"]
        cls.explosion(msg_manager, order_before)
        game_work.remove_props_event(prop_name=cls.name)
        situation = [
            f"{game_work.get_name(pl)}[hp {game_work.tmp[f'{pl}_old_hp']}->{game_work.tmp[f'{pl}_new_hp']}]."
            for pl in order_before
            if game_work.tmp[f"{pl}_old_hp"] != game_work.tmp[f"{pl}_new_hp"]
        ]
        situation_str = "\n".join(situation)
        if not game_work.flag_over:
            game_work.upsert_info(situation_str)
            draws = prop_data["data"]["draws"]
            for pl in game_work.order:
                game_work.draw_prop(pl, draws)
        return True

    @classmethod
    def callback(cls, msg_manager, moment, prop_data):
        if moment != "dead":
            return False
        game_work = GameWork.from_manager(msg_manager)
        current_data = game_work.get_prop_data(prop_name=cls.name)[0]
        current_data["data"]["reactivation"] += 1
        current_data["data"]["draws"] += 1
        return False

    @classmethod
    def explosion(cls, msg_manager, order_before):
        game_work = GameWork.from_manager(msg_manager)
        current_data = game_work.get_prop_data(prop_name=cls.name)[0]
        while current_data["data"]["reactivation"] > 0:
            current_data["data"]["reactivation"] -= 1
            for pl in order_before:
                if random.randint(1, 3) != 3:
                    game_work.damage(pl, 1, game_work.shooter)
                    game_work.tmp[f"{pl}_new_hp"] = game_work.tmp["new_hp"]
        return


# endregion
# class 和你爆了(PropComp, BaseProp):
#     name = "和你爆了"
#     helpdoc = ""
#     allow_flag = False
#     reply = []
