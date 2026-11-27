# 功能测试与覆盖率

本目录用 pytest 维护插件的回归测试：一个独立行为对应一个 `test_*` 函数，同一行为的不同输入
边界使用参数化或直接构造不同的对局数据，不把所有功能串在一条大型流程里。测试通过
`fakes.py` 里的假事件对象、对局构造器和临时 SQLite 数据库驱动核心逻辑，不依赖真实机器人账号、
真实对局、网络或本地开发者配置。

## 运行

要求 Python 3.11。插件导入依赖 `OlivOS`、`OlivaDiceCore` 与 `AmorLib`：

- `OlivOS`：通过 `OLIVOS_SOURCE` 指定其父目录，或 checkout 到 `.ci/OlivOS`；
- `OlivaDiceCore`：通过 `OLIVADICECORE_SOURCE` 指定其父目录，或 checkout 到 `.ci/OlivaDiceCore`；
- `AmorLib`：仓库内子模块，`git submodule update --init --recursive`。

本地运行：

```powershell
git submodule update --init --recursive

python -m pip install '.[test]'
python -m pytest tests -q
```

测试会把当前工作目录切到临时目录，写入测试临时目录和临时 SQLite 数据库，不会污染仓库或本机
插件数据。GUI 用例不在本目录维护；`MammonRoulette/GUI.py` 也不计入覆盖率。

## 覆盖率

```powershell
New-Item -ItemType Directory -Force test-results | Out-Null
python -m pytest tests `
  --cov=MammonRoulette `
  --cov-branch `
  --cov-context=test `
  --cov-report=term-missing `
  --cov-report=xml:test-results/coverage.xml `
  --cov-report=json:test-results/coverage.json `
  --cov-report=html:test-results/html `
  --junitxml=test-results/junit.xml
```

HTML 入口为 `test-results/html/index.html`，可查看每个文件已执行/未执行的语句与缺失分支。
XML 供覆盖率工具读取，JSON 用于统计，JUnit XML 提供通过、失败、错误和跳过数量。
统计范围为整个 `MammonRoulette/` 包，排除 `GUI.py`（见 `pyproject.toml` 的
`[tool.coverage.run]` 配置）。

2026-11-27 本地基线（Windows、Python 3.11）：**172 项通过，0 项失败**。
语句覆盖率 **100%**（1973/1973），分支覆盖率 **95.07%**（521/548），
综合覆盖率 **98.93%**。该数字不含 GUI，也不是 CI 的远端执行结果。

当前先建立真实基线，不设置未经评估的全仓库百分比门槛。后续优先用“先补失败的回归测试、
再修复”的方式推进，避免单纯用导入、常量断言或扩大排除项抬高数字。

## 功能与用例映射

| 功能范围 | 测试文件 | 检查内容 |
| --- | --- | --- |
| 包与清单 | `test_mammonroulette.py` | `app.json` 的命名空间/版本/优先级/消息模式/菜单，包级元数据，事件回调，命令注册 |
| 基础数据结构 | `test_core_base.py` | `Moment` 枚举、基础类默认行为、`PlayerView`/`GameState`/`BotAction` |
| 注册器与过滤器 | `test_core_registry.py` | `Registry`/`Entry`、状态/正则/名称过滤，模式/道具/效果/BOT 注册与查找 |
| 对局流程 | `test_core_work.py` | 加入/开局/装弹/射击/伤害/死亡/换人/结算、道具与效果事件、回复格式化 |
| 模式定义 | `test_defs_mode.py` | 经典/道具/金币/勇者/赌徒/大富翁的 start/join/shoot/damage/dead/try_over |
| 道具定义 | `test_defs_prop.py` | 各道具的 apply/can_use/on_moment/on_unregister、金币购买指令 |
| 效果定义 | `test_defs_effect.py` | 束缚、神经麻痹的 apply/on_moment 结算 |
| BOT 定义 | `test_defs_bot.py` | 达尔文 decide 分支、prop_can_use、BOT 行动循环 |
| 指令处理器 | `test_msgreply.py` | 签署/名片/排行/匹配/加入退出/射击/道具/投降/局势 |
| 配置与入口 | `test_config_main.py` | 配置读写、`Event` 回调、`unity_enabled`/`unity_reply` |
| 测试辅助 | `fakes.py`、`conftest.py` | 假事件对象、对局构造、临时数据库与依赖定位 |

## CI 与构建关系

`.github/workflows/ci.yml` 固定为 `ruff -> tests + coverage -> build`。前一步失败时后续任务不执行；
测试失败时仍会运行覆盖率汇总并上传报告。CI 在 `.ci/OlivOS` 与 `.ci/OlivaDiceCore` 下检出宿主与
核心依赖，并递归检出 `AmorLib` 子模块。
