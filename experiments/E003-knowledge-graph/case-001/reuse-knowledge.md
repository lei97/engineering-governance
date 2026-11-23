# Case 001 · 知识摘录

适用代码为 `83a21206ebf9e1addf6aa115a9f3c6427c2a40bf`。D1 至 D6 对应随任务分发的 `sources.json`。

| 主张 | 状态 | 内容与适用条件 | 证据 |
| --- | --- | --- | --- |
| C01 | 规则 | 此版本 Schema 的 `kind: requirement` 分支要求 `acceptance` 字段。 | D6:83–97 |
| C02 | 观察 | 原 `test_invalid` 在 `examples/invalid` 当批的完整错误字符串中搜索 `acceptance` 子串。 | D2:19–23 |
| C04 | 观察 | 此版本原反例 `missing-acceptance.yaml` 的记录 `REQ-005` 把 `SRC-001` 写作 `origin`。 | D4:1–6 |
| C05 | 观察 | 给定修订中 `examples/invalid` 的 ID 清单未列出 `SRC-001`。范围是这份清单。 | D5:1–6 |
| C07 | 观察 | 记录解析后已加入 `records`，且字符串 `origin` 既非记录自身 ID，也不在 `kind_by_id` 时，校验器报出含该记录路径的 `missing origin`。 | D3:62–65、72–75、78–85 |
| C08 | 推断 | 补齐合法 `acceptance` 后，若保留原文件名和原子串断言，且该记录仍生成缺失来源诊断，带有 `acceptance` 的文件名可使这一项子串断言通过。此处只判断 `acceptance` 单项。 | D2:19–23、D3:78–85、D4:1–6、D5:1–6 |

| 源 → 目标 | 谓词 | 范围 | 证据 |
| --- | --- | --- | --- |
| E04（原 REQ-005 反例）→ E06（`SRC-001`） | `references_as_origin` | 此版本原反例的 `origin` 字段。 | D4:1–6 |
| C05 → C08 | `contributes_to` | 当 `SRC-001` 确实未进入本次索引、记录仍引用它，且 C08 的文件名和断言条件成立时，来源缺失参与了这一条误通过路径。 | D2:19–23、D3:72–85、D4:1–6、D5:1–6 |
