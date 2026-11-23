# #16 历史材料

历史评审来自用户提供的《engineering-governance v0.1 改进候选清单（v3）》#16。该清单以 `9c38156fa8c277507ab30529af6d0480e8cbf833` 为基线。以下保留本任务相关表述。另有旧版和新版的代码快照。

## H1 · 问题描述摘录

> `validate_path` 先收集 Schema 错误，但之后仍然按预期类型使用 `kind` 和 `relations`：
> - `if kind in PREFIX`：`kind` 是列表时抛出 `TypeError: unhashable type`
> - `(record.get('relations') or {}).items()`：`relations` 是字符串或列表时抛出 `AttributeError`
>
> 一旦抛出异常，整个进程以 traceback 退出。CI 仍然会失败，但同批其他文件的诊断全部丢失，作者也看不到哪个文件的哪个字段出了问题。

## H2 · 复现表摘录

同目录另放一个合法 SRC 和一个独立出错的记录。

| 输入 | 结果 |
| --- | --- |
| `kind: [requirement]` | `TypeError: unhashable type: 'list'` |
| `relations: REQ-002` | `AttributeError: 'str' object has no attribute 'items'` |
| `relations: [verified_by]` | `AttributeError: 'list' object has no attribute 'items'` |
| `origin` 为列表 | 正常报告 Schema 错误 |
| `id` 为映射 | 正常报告 Schema 错误 |

## H3 · 历史验收建议摘录

> 字段类型不符时，跳过依赖该字段的跨记录检查，并且不重复报告同一处错误。

## H4 · 旧实现与样例定位

| 原始材料 | 版本及路径 |
| --- | --- |
| 索引创建与跨记录检查 | `9c38156: scripts/validate_truth.py` |
| 缺来源样例 | `9c38156: examples/invalid/dangling-reference.yaml` |
