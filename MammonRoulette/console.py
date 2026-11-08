# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/config.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

import copy
import json
import os

from AmorLib import IniConfig, releaseDir

from .custom import dictModeCustom, dictPropCustom, dictEffectCustom

MammonRoulette_name = "恶魔轮盘"
MammonRoulette_ver = "2.18.0-alpha"
MammonRoulette_svn = 58
MammonRoulette_ver_short = "%s(%s)" % (str(MammonRoulette_ver), str(MammonRoulette_svn))

debug = 0

dataDirRoot = "plugin/data/MammonRoulette"
configPath = "plugin/data/MammonRoulette/data/config.ini"

dbPath = "plugin/data/MammonRoulette/data/Roulette.db"
tmpGameDataPath = "plugin/tmp/MammonRoulette_data.json"
botModelDir = "plugin/data/MammonRoulette/data/botModel"


def initConfig(Proc):
    global dbPath, tmpGameDataPath, botModelDir
    if not os.path.exists(configPath):
        # 创建空配置文件
        with open(configPath, "w", encoding="utf-8") as f:
            f.write("")
    with IniConfig(configPath) as cfg:
        dbPath = cfg.get("path", "dbPath", "plugin/data/MammonRoulette/data/Roulette.db")
        tmpGameDataPath = cfg.get("path", "tmpGameDataPath", "plugin/tmp/MammonRoulette_data.json")
        botModelDir = cfg.get("dir", "botModelDir", "plugin/data/MammonRoulette/data/botModel")
    releaseDir(botModelDir)
    for hash_this in Proc.Proc_data["bot_info_dict"]:
        releaseDir(dataDirRoot + "/" + hash_this)


def readConfig(Proc):
    global dbPath, tmpGameDataPath, botModelDir
    with IniConfig(configPath) as cfg:
        dbPath = cfg.get("path", "dbPath", "plugin/data/MammonRoulette/data/Roulette.db")
        tmpGameDataPath = cfg.get("path", "tmpGameDataPath", "plugin/tmp/MammonRoulette_data.json")
        botModelDir = cfg.get("dir", "botModelDir", "plugin/data/MammonRoulette/data/botModel")
    for hash_this in Proc.Proc_data["bot_info_dict"]:
        custom_path = dataDirRoot + "/" + hash_this
        releaseDir(custom_path)
        dictModeCustom[hash_this] = copy.deepcopy(dictModeCustom["default"])
        dictPropCustom[hash_this] = copy.deepcopy(dictPropCustom["default"])
        dictEffectCustom[hash_this] = copy.deepcopy(dictEffectCustom["default"])
        try:
            with open(custom_path + "/customMode.json", "r", encoding="utf-8") as f:
                customDefs = json.load(f)
                dictModeCustom[hash_this].update(customDefs)
        except:
            pass
        try:
            with open(custom_path + "/customProp.json", "r", encoding="utf-8") as f:
                customDefs = json.load(f)
                dictPropCustom[hash_this].update(customDefs)
        except:
            pass
        try:
            with open(custom_path + "/customEffect.json", "r", encoding="utf-8") as f:
                customDefs = json.load(f)
                dictEffectCustom[hash_this].update(customDefs)
        except:
            pass


def saveConfig(Proc):
    with IniConfig(configPath) as cfg:
        cfg.set("path", "dbPath", dbPath)
        cfg.set("path", "tmpGameDataPath", tmpGameDataPath)
        cfg.set("dir", "botModelDir", botModelDir)
        cfg.save()
    for hash_this in Proc.Proc_data["bot_info_dict"]:
        custom_path = dataDirRoot + "/" + hash_this
        releaseDir(custom_path)
        with open(custom_path + "/customMode.json", "w", encoding="utf-8") as f:
            json.dump(dictModeCustom[hash_this], f, ensure_ascii=False, indent=4)
        with open(custom_path + "/customProp.json", "w", encoding="utf-8") as f:
            json.dump(dictPropCustom[hash_this], f, ensure_ascii=False, indent=4)
        with open(custom_path + "/customEffect.json", "w", encoding="utf-8") as f:
            json.dump(dictEffectCustom[hash_this], f, ensure_ascii=False, indent=4)
