# E003 · 工程知识图谱构建与验证

本仓库已用 E002 记录时间语义实验，因此将对话中的知识图谱实验编号为 E003。首轮核对从原始材料提取的实体、主张和有向关系能否回到证据。通过 Apollo 基线检查管线，再用一个真实工程缺陷检验提取质量。 [讨论来源](chatgpt-conversation://6b0141a3-4e6c-83ec-8546-2139db0306b6)

## P0 · Cookbook 替代模型试跑

上游固定在 `8ad5de647d4f0f50c95d74aabc8aa20a3f70cdd3`。2026-11-23 获取六篇 Wikipedia REST 摘要，保存原文、接口与修订号。语料来自对应 Wikipedia 条目的贡献者，按 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 提供。每一条的修订号可用作 `https://en.wikipedia.org/w/index.php?oldid=<revision>` 的版本入口。 [官方教程](https://platform.claude.com/cookbook/capabilities-knowledge-graph-guide) · [固定版本的示例和评估](https://github.com/anthropics/claude-cookbooks/tree/8ad5de647d4f0f50c95d74aabc8aa20a3f70cdd3/capabilities/knowledge_graph) · [冻结语料](baseline/corpus.json)

环境未配置 Anthropic API 凭据。两个独立 Codex 会话各按 notebook 的提取提示处理三篇摘要，随后由第三个会话按原消歧提示对各类型分组。模型采用 `gpt-6.2-sol` 的默认配置，同一批三篇共享会话。提取输出回放到上游独立评分函数，图数据逐项与上游 notebook 的图构建单元一致。Claude 原模型、摘要生成与多跳问答未在这次试跑中实测。 [提取记录](baseline/extraction.json) · [消歧记录](baseline/clusters.json) · [图与指标](baseline/result.json)

六篇共得到 40 个实体提及和 49 条关系。24 个不同名称合为 22 个节点，49 条边保留文档来源。消歧对每种类型均覆盖全部输入名称。这里只核对名称覆盖和实际合并，实体身份质量尚无独立金标。

| 指标 | 宏平均 P | 宏平均 R | 宏平均 F1 |
| --- | ---: | ---: | ---: |
| 实体名称 | 0.929 | 0.460 | 0.606 |
| 关系两端（上游口径） | 0.750 | 0.310 | 0.422 |
| 完整三元组（谓词字面匹配） | 0.333 | 0.127 | 0.178 |

宏平均只用上游有标注的 `Apollo 11` 和 `Neil Armstrong` 两篇。获取的摘要和标签可见范围有差异，例如何者参与 Gemini 8 并未出现在本次 Neil Armstrong 摘要中。词面三元组会漏掉同义谓词。将参考边的谓词全部换成错误标签后，两篇的上游端点 F1 仍为 `1.00`，字面三元组 F1 为 `0.00`。工程案例单独评阅谓词、方向和证据。

在 Python 3.12 和 NetworkX 3.7 下，从仓库根目录执行以下命令可以重算图和指标。`<cookbook-data>` 是上述固定提交中 `capabilities/knowledge_graph/data` 的本地目录，含 `alias_map.json` 和 `sample_triples.json`。

```sh
python -B experiments/E003-knowledge-graph/baseline/replay.py /path/to/cookbook/capabilities/knowledge_graph/data
```

| 上游文件 | SHA-256 |
| --- | --- |
| `guide.ipynb` | `7e6978a4561266303de038f100d34e38c285abbe8bf962971d5cd45ed8d13c82` |
| `evaluation/eval_extraction.py` | `3df9802d8a19b15042ea5eada51e990a195cc7d45c9b19fce63d6a77debaa5ed` |
| `data/alias_map.json` | `659682c5e3af948be4cd4796e538398be25b006915ef928865a2ab194ca3bd1a` |
| `data/sample_triples.json` | `c7111dc9358004f8be6965abee034a0df31d200d3e11210afdd2893ea5196248` |

## P1 · 真实工程案例

首例使用本仓库 #13 的反例测试误通过问题，选择依据是有可回溯的评审、修复前代码和可运行的前后证据。提取会话只收到修复前提交 `83a2120` 的片段和 v3 评审中的问题与复现描述。候选判据及修复提交 `093f88d` 单独留出。该案例用于试跑证据追溯，异步设备生命周期案例仍待取得材料。 [修复前输入](case-001/sources.json) · [候选判据](case-001/reference.json) · [留出复跑](case-001/holdout.json)

留出复跑分别从两个提交取得临时副本，再给 `missing-acceptance.yaml` 加入合法验收项。修复前原测试仍通过，目标文件只有缺失来源的报错。修复后原反例断言失败，目标文件没有诊断。同批其他反例仍使校验命令退出 `1`。这些运行结果由提取以外的复跑获得。

## P2 · 首例证据复核

提取会话生成 10 个实体、10 条主张和 12 条有向关系。它把评审报告的运行结果与从代码推导的误命中机制分别建模。程序核对了关系端点和全部证据行号。另一独立 Agent 按原始片段复核内容支持、状态、谓词和方向。 [候选工程知识图](case-001/extraction.json) · [逐条评阅](case-001/evaluation.json)

| 核对项 | 首例结果 |
| --- | --- |
| 主张与状态 | 10/10 条获证据支持，报告、观察、推断和规则的归类与材料一致。 |
| 有向关系 | 11 条获支持，1 条部分获支持。`can_satisfy` 的源是诊断类别，证据实际支持的是带特定文件路径的诊断实例。目标是描述断言的主张，关系真正指向的是其中的子串检查条件。 |
| 候选参考覆盖 | 六项参考主张的信息均可定位。其中两项需要组合多条主张，补齐验收项后的误通过机制没有单条完整的条件推断。两条候选参考关系中，一条由拆开的两条边表达，另一条缺少同方向的显式边。 |

引用可解析只说明原文能找到。证据支持、关系方向及语义仍需逐项复核。本轮是单个已修复缺陷上的 Agent 初评，候选判据待人工确认，尚无复用收益或审阅工时数据。
