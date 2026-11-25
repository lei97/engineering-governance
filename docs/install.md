# 在其他项目中使用 Engineering Governance

| 分发包 | 内容 | 适用任务 |
| --- | --- | --- |
| `light` | Skill、模式参考与治理摘要 | 用 Agent 梳理任务边界、需求解释和工作证据 |
| `full` | 轻量包的全部内容、权威规范、Schema、校验器与依赖清单 | 需要查阅完整规范或验证项目真源记录 |

## 构建与安装

已有 ZIP 的使用者可以直接解压。维护者在 Engineering Governance 源码目录运行构建命令，选择所需的分发包与尚未使用的输出路径。

```sh
python3 scripts/build_distribution.py light /tmp/engineering-governance-light.zip
python3 scripts/build_distribution.py full /tmp/engineering-governance-full.zip
```

下例将完整包解压到 `/tmp/engineering-governance-full`，其中包含本指南。轻量包可按同样方式解压。

```sh
python3 -m zipfile -e /tmp/engineering-governance-full.zip /tmp/engineering-governance-full
```

将解压后的 `skills/engineering-governance/` 目录安装或链接到当前 Agent 宿主的 Skill 搜索路径，保留目录内的 `SKILL.md` 和 `references/`。使用完整包时，向 Agent 提供完整包解压根目录，或在启动 Agent 的环境中设置 `ENGINEERING_GOVERNANCE_ROOT`。在源码树或完整包内直接使用 Skill 时，也可以从其真实文件路径定位根目录。

## 在目标项目中验证 YAML

各项目维护自己的 `truth/`。以下命令在目标项目根目录执行。已有虚拟环境时，直接激活并使用它执行依赖安装和校验。

```sh
export ENGINEERING_GOVERNANCE_ROOT=/tmp/engineering-governance-full
python3 -m venv /tmp/engineering-governance-venv
. /tmp/engineering-governance-venv/bin/activate
python3 -m pip install -r "$ENGINEERING_GOVERNANCE_ROOT/requirements.txt"
python3 "$ENGINEERING_GOVERNANCE_ROOT/scripts/validate_truth.py" "$PWD/truth"
```

将 `"$PWD/truth"` 换成项目实际使用的记录目录。命令以 `PASS` 或 `FAIL` 汇总结构和引用检查，出错时返回非零值并报告相关文件。涉及已确认需求时，仍需按规范核对需求含义与验收依据。
