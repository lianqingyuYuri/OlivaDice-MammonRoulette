# -*- encoding: utf-8 -*-
# ruff: isort: skip_file
"""
@File      :    MammonRoulette/__init__.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

MammonRoulette_name = "恶魔轮盘"
MammonRoulette_ver = "2.19.0-alpha"
MammonRoulette_svn = 61
MammonRoulette_ver_short = f"{str(MammonRoulette_ver)}({str(MammonRoulette_svn)})"

from . import Core
from .Core.event import command
from . import Defs

from . import main
from . import custom
from . import config
from . import msgReply

from AmorLib import has_NativeGUI

if has_NativeGUI:
    from . import GUI
