# Case 001 · 人工复核底稿

本表列出实际抽取内容和独立 Agent 初评，末列留给人审。逐项填写保留、改写或排除。改写时记录更正后的内容、适用提交或条件以及原文依据。复用实验仅使用人工确认的子集。实验裁定的适用范围为本案例。

[修复前原文 D1–D6](sources.json) · [提取原文](extraction.json) · [Agent 逐项初评](evaluation.json) · [独立留出复跑](holdout.json)

优先核对三个边界。C05 的原文是修复前批次的 ID 清单。C08 依代码推断子串误命中，C09 记录评审报告。留出复跑可以支持一条独立的运行观察，保留各自证据。E08 指诊断类别，关系实际需要定位到具体诊断实例与布尔检查条件。

## 主张

| 编号 | 原主张 | 状态 | 原文定位 | Agent 初评 | 人工裁定与修订 |
| --- | --- | --- | --- | --- | --- |
| C01 | 当记录的 kind 为 requirement 时，schema 要求包含 acceptance 字段。 | 规则 | D6:81–99 | 支持 | 待填 |
| C02 | test_invalid 的 acceptance 断言在整个 examples/invalid/ 的错误列表中搜索 acceptance 子串。 | 观察 | D2:19–23 | 支持 | 待填 |
| C03 | REQ-005 反例未声明 acceptance 字段。 | 观察 | D4:1–6 | 支持 | 待填 |
| C04 | REQ-005 的 origin 指向 SRC-001。 | 观察 | D4:1–6 | 支持 | 待填 |
| C05 | 给定的 examples/invalid/ ID 清单未列出 SRC-001。 | 观察 | D5:1–6 | 支持 | 待填 |
| C06 | validate_path 把文件路径写入 schema 校验错误字符串。 | 观察 | D3:62–63 | 支持 | 待填 |
| C07 | 当字符串 origin 既不等于当前记录 ID 又不在已登记 ID 中时，validate_path 添加带文件路径的 missing origin 错误。 | 观察 | D3:72–75、D3:78–85 | 支持 | 待填 |
| C08 | REQ-005 的 missing origin SRC-001 错误可凭文件名中的 acceptance 满足该子串断言。 | 推断 | D2:20–23、D3:78–85、D4:1–6、D5:1–6 | 支持 | 待填 |
| C09 | 评审记录称，给 missing-acceptance.yaml 补上合法的 acceptance 后，原测试仍然通过。 | 报告 | D1:94–97 | 支持 | 待填 |
| C10 | 该断言无法单独验证 REQ-005 是否触发缺少 acceptance 的 schema 错误。 | 推断 | D2:20–23、D3:78–85、D4:1–6、D5:1–6、D6:81–99 | 支持 | 待填 |

## 有向关系

| 源 → 目标 | 谓词 | 原文定位 | Agent 初评 | 人工裁定与适用范围 |
| --- | --- | --- | --- | --- |
| `E03` schemas/knowledge.schema.json → `E05` acceptance | `requires_for_requirements` | D6:81–99 | 支持 | 待填 |
| `E01` tests/test_validation.py::test_invalid → `E07` examples/invalid/ | `validates` | D2:19–20 | 支持 | 待填 |
| `E01` tests/test_validation.py::test_invalid → `E05` acceptance | `searches_diagnostics_for_field_name` | D2:20–23 | 支持 | 待填 |
| `E04` examples/invalid/missing-acceptance.yaml (REQ-005) → `E05` acceptance | `omits_field` | D4:1–6 | 支持 | 待填 |
| `E04` examples/invalid/missing-acceptance.yaml (REQ-005) → `E06` SRC-001 | `references_as_origin` | D4:1–6 | 支持 | 待填 |
| `E02` scripts/validate_truth.py::validate_path → `E09` 带文件路径的 schema 校验诊断 | `emits` | D3:62–63 | 支持 | 待填 |
| `E02` scripts/validate_truth.py::validate_path → `E08` missing origin | `emits_for_unregistered_origin` | D3:78–85 | 支持 | 待填 |
| `C04` → `C08` | `contributes_to` | D4:1–6、D3:78–85 | 支持 | 待填 |
| `C05` → `C08` | `contributes_to` | D5:1–6、D3:78–85 | 支持 | 待填 |
| `E08` missing origin → `C02` | `can_satisfy` | D2:22–23、D3:78–85、D4:1–6、D5:1–6 | 部分支持 | 待填 |
| `E10` v3 评审清单 #13 → `C09` | `reports` | D1:94–97 | 支持 | 待填 |
| `C08` → `C10` | `supports` | D2:22–23、D3:78–85、D4:1–6、D5:1–6、D6:81–99 | 支持 | 待填 |

## 覆盖率基线

一位独立标注者仅从 D1–D6 列出 10 条必要主张和 4 条有向关系。标注会话没有收到候选图谱、首次评阅或修复后的材料。先确认这份候选清单是否覆盖会影响修复或验收的知识，再确认每项的状态、适用范围和关系方向。以下以参考清单编号开头，映射到已提取图谱的编号。 [独立参考清单](independent-reference.json)

| 参考编号 | 已提取对应 | 原子主张覆盖初核 |
| --- | --- | --- |
| C01 | C01 | 命中。requirement 必须有验收字段。 |
| C02 | C03 | 命中。原反例缺少验收字段。 |
| C03 | C04 | 命中。原反例引用 SRC-001。 |
| C04 | C05 | 命中。所给目录清单没有 SRC-001。 |
| C05 | C07 | 命中。未找到来源时附路径报错。适用范围另要核对记录已进入 `records`。 |
| C06 | C02 | 命中。原断言做全批子串搜索。 |
| C07 | — | 遗漏。合法补齐验收字段消除该缺字段条件的推断未单列。 |
| C08 | C08、C09 | 部分。原图给出了误命中机制和补齐字段后的通过报告。未单列在原路径、原引用及来源索引仍缺失时，补齐字段后仍报 `missing origin` 的条件推断。 |
| C09 | C08 | 命中。单条缺失来源诊断里的文件名足以满足 `acceptance` 这一项子串检查。 |
| C10 | C09 | 命中。整组断言通过是评审者报告的复现。 |

按明确覆盖计为 8/10，另有 1 项部分覆盖、1 项遗漏。四条参考关系保留供人工对齐。已有 `can_satisfy` 边触及参考 C08 → C09 的机制，但源是诊断类别，目标是描述断言的主张。其余关系的端点或条件尚缺直接对应。正式语义 Triple F1 需要先确认实体和等义谓词对应以及适用范围。

## 拟供第一轮复用的子集

请优先确认 `C01`、`C02`、`C04`、`C05`、`C07` 和 `C08`，以及 `E04 references_as_origin E06`、`C05 contributes_to C08`。只放入通过人工复核的条目。范围限定在 `83a2120` 的反例测试及该批次。C05 依据给定清单。C07 要求记录已被解析并加入 `records`。C08 是推断，仅就 `acceptance` 单项，要求保留带该词的文件名、原始断言和未解析的来源诊断。 [知识复用对照草案](reuse-protocol.md)
