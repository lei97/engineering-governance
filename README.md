# Engineering Governance — v0.1 (experimental)

面向人和 Agent 参与的软件工程：用可审查的约束、最小真源记录和可重复的实验，维持工程活动的透明性、连续性与可恢复性。

**状态：探索性原型，不是已验证的行业规范。** 不承诺 YAML 能消除自然语言歧义，也不默认代码能够从需求无损再生。

## 快速验证

```bash
python -m pip install -r requirements.txt
python scripts/validate_truth.py truth
python scripts/validate_truth.py examples/valid
python scripts/validate_truth.py examples/invalid  # 应当失败
python -m unittest discover -s tests -v
```

验证器可检查限定 YAML 语法、Schema 结构、全局 ID 唯一性、引用存在性、类型匹配、非自引用；无法证明需求符合人的真实意图。

## 仓库导览

- `skills/engineering-governance/SKILL.md`：可移植 Skill 入口；根据任务按需读取五种模式。
- `specifications/`：权威规范草案，Skill 不重复定义规则。
- `schemas/knowledge.schema.json`：真源记录的结构契约。
- 本仓库已确认的目标与首轮范围存于 `truth/`，各自引用作者原话。[表达目标 REQ-100](truth/REQ-100.yaml) · [首轮范围 REQ-101](truth/REQ-101.yaml)
- `examples/valid/` 与 `examples/invalid/`：正反样例。
- `experiments/E001/`：人工 + Agent 对照验证协议。
- `scripts/validate_truth.py`：确定性检查，不调用 LLM。
- `research/references.md`：外部资料与采用边界。

## 使用于其他项目

将 `skills/engineering-governance/` 安装/链接到所用 Agent 支持的 Skill 目录，并在项目中自行建立 `truth/`；不要把本仓库 `examples/` 当成项目真源。不同 Agent 宿主的发现/安装路径可能不同，请按其官方文档配置。

## 设计边界

- 项目知识归项目所有；Skill 只定义治理方法。
- 真实任务必须先识别约束和工作区状态，保护未提交改动。
- `accepted` 仅代表需求获授权确认，不代表已实现或已通过测试。
- 逆向得到的是行为观察或推断，不能直接升级为正式需求。
- E001 没有预设获胜方案：比较 YAML、Markdown 与无显式索引方案。

## 后续候选

v0.2 再考虑生命周期转换、权威冲突解析、双向追溯、变更影响图、复杂引用关系及多模型一致性统计。

## 来源

见 `research/references.md`。本工程的 YAML profile 比 YAML 1.2.2 更严格，属于本仓库的约定，不是 YAML 官方的强制要求。
