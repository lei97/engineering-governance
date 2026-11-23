# 历史交接摘要

下列条目均定位于 `9c38156fa8c277507ab30529af6d0480e8cbf833`。

- **K1** 在已解析记录以字符串 ID 进入首条记录索引、字符串 `origin` 非自身 ID 且不在索引内，并执行到来源检查时，批次校验器收集缺来源 ID 诊断。旧代码行为。依据 H4 · `scripts/validate_truth.py:60–79`。
- **K2** 对复现表所列 `relations: REQ-002`，批次校验器抛出未捕获 `AttributeError`。历史复现记录。依据 H2 · 第二行数据。
- **K3** 历史问题描述称，当 `relations` 为字符串或列表时，批次校验器抛出未捕获 `AttributeError`。历史问题陈述。依据 H1 · `relations` 条目。
- **K4** 对复现表所列 `kind: [requirement]`，批次校验器抛出未捕获 `TypeError`。历史复现记录。依据 H2 · 第一行数据。
- **K5** 在 Schema 校验后读到非字符串 `id` 时，非字符串 ID 的已解析记录不进入批次首条记录索引。旧代码行为。依据 H4 · `scripts/validate_truth.py:60–72`。
- **K6** 第一轮记录处理结束后进入第二轮时，旧版后续跨记录检查遍历批次首条记录索引。旧代码行为。依据 H4 · `scripts/validate_truth.py:72–87`。
