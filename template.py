key = "group_id"
game = {
    "start": bool,  # false 准备阶段、true 正式游戏
    "over": bool,  # false 游戏中、true 游戏结束
    "expireTime": int,  # 过期时间
    "seats": int,  # 席位
    "mode": {
        "name": str,  # 游戏模式名称
        "points": int,  # 积分
        "props": {
            "pool": [],  # 道具池
            "allow": [],  # 道具白名单
            "ban": [],  # 道具黑名单
            "limit": int,  # 持有道具上限
        },
    },
    "data": {
        "ammo_live": int,  # 实弹数
        "ammo_blank": int,  # 空弹数
        "bullet": int,  # 当前子弹
        "shooter": str,  # 枪手
        "order": [],  # 行动顺序
        "players": {
            "user_id": {
                "name": str,
                "hp": int,
                "props": [],
                "actions": int,
                "kills": int,
                "suicide": bool,  # 自杀
                "surrender": bool,  # 投降
                "points_mult": int,  # 积分倍率
                "effects_event": {},  # 效果事件
                "bot_model": None,  # BOT模型
            },
        },
        "modify": {
            "dmg": int,  # 伤害
            "flag_ammo_show": bool,  # 显示弹药
            "flag_bullet_show": bool,  # 显示子弹
            "flag_bot": bool,  # AI旗帜
        },
        "props_event": [],  # 道具事件
    },
    "reply": {
        "info": [],  # 常规信息
        "note": {
            "flag_ammo": bool,  # 弹药消息
            "flag_shooter": bool,  # 枪手信息
        },  # 分割线以下的消息
        "only": "",  # 会覆盖其他消息
    },
    "tmp": {
        "target": str,  # 目标玩家ID
        "source": str,  # 来源玩家ID
        "is_shoot_me": bool,  # 是否射击自己
        "is_attack_me": bool,  # 是否攻击自己
        "dmg": int,  # 伤害值
        "dmg_type": str,  # 伤害类型
        "consume_action": bool,  # 消耗行动力（None/0/1）
        "new_hp": int,  # 新血量
        "old_hp": int,  # 旧血量
        "is_dead": bool,  # 是否死亡
        "is_check_dead": bool,  # 是否检查死亡
    },
}

moment = [
    "reload",
    "shoot",
    "damage",
    "dead",
    "done",
    "switch",
]
# 特殊事件
remove_props_event = "remove"
remove_effects_event = "remove"

prop_data = {
    "id": str,  # 道具id
    "name": str,  # 道具名称
    "data": {},  # 道具数据
}
key = "effect"
effect_data = {"stacks": int, "data": {}}
