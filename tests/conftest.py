"""Bootstrap for the MammonRoulette contract tests."""

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = Path(__file__).resolve().parent
ORIGINAL_CWD = Path.cwd()
BOOTSTRAP_DIRECTORY = None


def _resolve_olivos_source():
    candidates = []
    configured = os.environ.get("OLIVOS_SOURCE")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend(
        [
            REPO_ROOT / ".ci" / "OlivOS",
            REPO_ROOT.parent / "OlivOS-dev",
            REPO_ROOT.parent / "OlivOS",
        ]
    )
    for candidate in candidates:
        if (candidate / "OlivOS" / "__init__.py").is_file():
            return candidate.resolve()
    spec = importlib.util.find_spec("OlivOS")
    if spec and spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations))).resolve().parent
    return None


def _resolve_olivadicecore_source():
    """返回 OlivaDiceCore 包的父目录，使 `import OlivaDiceCore` 可用。"""
    candidates = []
    configured = os.environ.get("OLIVADICECORE_SOURCE")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend(
        [
            REPO_ROOT / ".ci",  # CI：仓库根即插件包，checkout 到 .ci/OlivaDiceCore
            REPO_ROOT / ".ci" / "OlivaDiceCore",  # 兜底：仓库内再套一层 OlivaDiceCore 目录
            REPO_ROOT.parent / "OlivaDice",  # 本地：OlivaDice/OlivaDiceCore
        ]
    )
    for candidate in candidates:
        if (candidate / "OlivaDiceCore" / "__init__.py").is_file():
            return candidate.resolve()
    spec = importlib.util.find_spec("OlivaDiceCore")
    if spec and spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations))).resolve().parent
    return None


OLIVOS_SOURCE = _resolve_olivos_source()
OLIVADICECORE_SOURCE = _resolve_olivadicecore_source()
AMORLIB_SOURCE = REPO_ROOT / "OlivOS-AmorLib"

for entry in (str(TESTS_ROOT), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)
if OLIVOS_SOURCE is not None and str(OLIVOS_SOURCE) not in sys.path:
    sys.path.insert(0, str(OLIVOS_SOURCE))
if OLIVADICECORE_SOURCE is not None and str(OLIVADICECORE_SOURCE) not in sys.path:
    sys.path.insert(0, str(OLIVADICECORE_SOURCE))
if (AMORLIB_SOURCE / "AmorLib" / "__init__.py").is_file() and str(AMORLIB_SOURCE) not in sys.path:
    sys.path.insert(0, str(AMORLIB_SOURCE))


def pytest_configure(config):
    if OLIVOS_SOURCE is None:
        raise pytest.UsageError("未找到 OlivOS 源码。请设置 OLIVOS_SOURCE，或把主机仓库 checkout 到 .ci/OlivOS。")
    if OLIVADICECORE_SOURCE is None:
        raise pytest.UsageError("未找到 OlivaDiceCore 源码。请设置 OLIVADICECORE_SOURCE，或 checkout 到 .ci/OlivaDiceCore。")
    if not (AMORLIB_SOURCE / "AmorLib" / "__init__.py").is_file():
        raise pytest.UsageError("未找到 AmorLib 子模块。请运行 git submodule update --init --recursive。")


def pytest_sessionstart(session):
    global BOOTSTRAP_DIRECTORY
    # 导入 OlivOS 会按当前工作目录创建空的 lib/、plugin/ 等目录。
    BOOTSTRAP_DIRECTORY = tempfile.TemporaryDirectory(prefix="olivos-mammonroulette-tests-")
    os.chdir(BOOTSTRAP_DIRECTORY.name)


def pytest_collection_finish(session):
    os.chdir(ORIGINAL_CWD)


def pytest_sessionfinish(session, exitstatus):
    os.chdir(ORIGINAL_CWD)
    if BOOTSTRAP_DIRECTORY is not None:
        BOOTSTRAP_DIRECTORY.cleanup()


@pytest.fixture(autouse=True)
def isolated_installation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ("OLIVOS_WEBUI_HOST", "OLIVOS_WEBUI_PORT"):
        monkeypatch.delenv(name, raising=False)
