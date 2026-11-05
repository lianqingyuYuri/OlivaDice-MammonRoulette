# -*- encoding: utf-8 -*-
"""
@File      :    MammonRoulette/__init__.py
@Author    :    lianqingyuYuri恋倾雨
@Contact   :    xinghu2408@foxmail.com
@License   :    AGPLv3
@Copyright :    (C) 2026 MammonRoulette
@Desc      :    None
"""

from . import console

from . import Core
from . import Defs

from . import main
from . import msgCustom
from . import msgReply

from AmorLib import has_NativeGUI

if has_NativeGUI:
    from . import GUI
