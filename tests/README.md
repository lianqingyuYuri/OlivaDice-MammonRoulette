# MammonRoulette 测试

这里保留一组最小的契约测试，用来确认以下内容没有被改坏：

- `app.json` 的命名空间、版本、优先级、消息模式与菜单声明；
- 包级元数据（插件名 / 版本 / svn）；
- `main.Event` 的常用回调入口；
- 基于 `CommandRegistry` 的指令注册表（`signed`、`card`、`shoot`、`surrender` 等）。

业务测试应在本目录继续添加。不要把真实账号、真实对局或本地开发者配置写进测试。

## 依赖

插件导入依赖 `OlivOS`、`OlivaDiceCore` 与 `AmorLib` 子模块：

- `OlivOS`：通过 `OLIVOS_SOURCE` 指定其父目录，或 checkout 到 `.ci/OlivOS`；
- `OlivaDiceCore`：通过 `OLIVADICECORE_SOURCE` 指定其父目录，或 checkout 到 `.ci/OlivaDiceCore`；
- `AmorLib`：仓库内子模块，`git submodule update --init --recursive`。

## 本地运行

```powershell
git submodule update --init --recursive

python -m pytest tests -q
```

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

覆盖率默认不设门槛；稳定后可以自行加入 `--cov-fail-under`。

## CI 顺序

`.github/workflows/ci.yml` 固定为 `ruff -> tests + coverage -> build`，前一步失败时后续任务不会执行。