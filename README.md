# Engineering Governance — v0.1 (experimental)

Engineering Governance 是供需求作者和 Agent 共用的工程治理 Skill。v0.1 首先检验，在需求已经确认的前提下，用简洁、受约束的 YAML 管理需求真源，能否减少解读时的隐含假设、歧义和遗漏。

**当前为实验原型。** E001 和 E002 已完成各自的案例对照。现行 Schema 继续作为实验基线。下一步从真实工程案例中查找现有表达的失效边界。 [两轮实验联合复盘](docs/v0.1-experiment-retrospective.md) · [v0.1 版本确认记录](docs/v0.1-review.md)

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
- E001 首轮的任务、评阅方法和记录模板见[需求解释对照](experiments/E001/README.md)。
- `scripts/validate_truth.py`：确定性检查，不调用 LLM。
- `research/references.md`：外部资料与采用边界。

## 使用于其他项目

将 `skills/engineering-governance/` 安装/链接到所用 Agent 支持的 Skill 目录，并在项目中自行建立 `truth/`；不要把本仓库 `examples/` 当成项目真源。不同 Agent 宿主的发现/安装路径可能不同，请按其官方文档配置。

## 设计边界

- 项目知识归项目所有；Skill 只定义治理方法。
- 真实任务必须先识别约束和工作区状态，保护未提交改动。
- `accepted` 仅代表需求获授权确认，不代表已实现或已通过测试。
- 逆向得到的是行为观察或推断，不能直接升级为正式需求。
- 原包比较 Markdown、YAML 与代码及零散注释的三组协议已保留，供后续研究真源识别与冲突处理。[原三组协议](experiments/E001/truth-identification/README.md)

## 后续候选

v0.2 再考虑生命周期转换、权威冲突解析、双向追溯、变更影响图、复杂引用关系及多模型一致性统计。

## 来源

见 `research/references.md`。本工程的 YAML profile 比 YAML 1.2.2 更严格，属于本仓库的约定，不是 YAML 官方的强制要求。
