# 校验器版本交接复核

旧版为 `9c38156fa8c277507ab30529af6d0480e8cbf833`，目标新版为 `83a21206ebf9e1addf6aa115a9f3c6427c2a40bf`，对应下文的 `source/old` 和 `source/new`。两版的 Schema 和所附规范内容相同。

## 七批逐版结果

对外输出依据 `evidence.json` 对应批次的 `results.old` 和 `results.new`。十四次运行的退出码均为 1。表中的「完成」表示批次正常返回诊断并打印摘要，摘要仍为 `FAIL`。末列的执行过程根据快照源码推断。下表用 A 指 `a/SRC-001.yaml`、B 指 `b/REQ-005.yaml`、Z 指 `z/REQ-004.yaml`。

| 批次 | 版本 | 是否完成、未捕获异常、stdout 正常摘要 | stderr 实际文件诊断 | 源码所示检查过程 |
| --- | --- | --- | --- | --- |
| 1 | 旧 | 完成，无异常，`FAIL: 1 YAML records; 1 errors` | `REQ-004.yaml`：`missing origin SRC-999` | Schema 无报错。执行来源查找，索引无 `SRC-999`。没有关系目标可查。 |
| 1 | 新 | 完成，无异常，`FAIL: 1 YAML records; 1 errors` | `REQ-004.yaml`：`missing origin SRC-999` | Schema 无报错。执行来源查找，索引无 `SRC-999`。缺少 `relations`，跳过关系检查。 |
| 2 | 旧 | 中止，`AttributeError: 'str' object has no attribute 'items'`，stdout 空 | 仅 traceback，无文件诊断 | A、Z 均完成 Schema 检查，A 的 `relations` 错误已收集。第二轮 A 无 `origin`，其非空字符串 `relations` 触发异常，Z 的来源检查未到达。 |
| 2 | 新 | 完成，无异常，`FAIL: 2 YAML records; 2 errors` | A `[relations]`：`'REQ-002' is not of type 'object'`；Z：`missing origin SRC-999` | A 无 `origin`，其非对象的关系检查被跳过。Z 的来源检查执行并报错。 |
| 3 | 旧 | 中止，`TypeError: unhashable type: 'list'`，stdout 空 | 仅 traceback，无文件诊断 | 第一轮已收集 A 的 `kind` 枚举错误，并以字符串 ID 登记 A，随后在 `kind in PREFIX` 抛错。B、Z 的 Schema 检查以及整个跨记录阶段均未到达。 |
| 3 | 新 | 完成，无异常，`FAIL: 3 YAML records; 2 errors` | A `[kind]`：`['source']` 不满足枚举；Z：`missing origin SRC-999` | A 以 `SRC-001` 入索引，索引种类为 `None`，跳过 ID 前缀与种类的一致性检查。B 查到 `SRC-001`，跳过依赖该目标种类的诊断。Z 的来源检查执行并报错。 |
| 4 | 旧 | 完成，无异常，`FAIL: 2 YAML records; 2 errors` | B：`missing origin SRC-001`；Z：`missing origin SRC-999` | 批次没有 A。B、Z 均通过 Schema，分别查找来源，两个 ID 都不在索引。 |
| 4 | 新 | 完成，无异常，`FAIL: 2 YAML records; 2 errors` | B：`missing origin SRC-001`；Z：`missing origin SRC-999` | 批次没有 A。B、Z 均通过 Schema，分别查找来源，两个 ID 都不在索引。 |
| 5 | 旧 | 完成，无异常，`FAIL: 2 YAML records; 2 errors` | A `[relations]`：`[] is not of type 'object'`；Z：`missing origin SRC-999` | A 无 `origin`。空列表经 `or {}` 回退为空字典，其 `.items()` 无条目。Z 的来源检查执行并报错。 |
| 5 | 新 | 完成，无异常，`FAIL: 2 YAML records; 2 errors` | A `[relations]`：`[] is not of type 'object'`；Z：`missing origin SRC-999` | A 无 `origin`。空列表因非字典而跳过关系检查。Z 的来源检查执行并报错。 |
| 6 | 旧 | 中止，`AttributeError: 'list' object has no attribute 'items'`，stdout 空 | 仅 traceback，无文件诊断 | A、Z 均完成 Schema 检查，A 的 `relations` 错误已收集。第二轮 A 无 `origin`，其非空列表触发异常，Z 的来源检查未到达。 |
| 6 | 新 | 完成，无异常，`FAIL: 2 YAML records; 2 errors` | A `[relations]`：`['REQ-002'] is not of type 'object'`；Z：`missing origin SRC-999` | A 无 `origin`，其非字典的关系检查被跳过。Z 的来源检查执行并报错。 |
| 7 | 旧 | 完成，无异常，`FAIL: 3 YAML records; 3 errors` | A `[id]`：`{'bad': 'SRC-001'} is not of type 'string'`；B：`missing origin SRC-001`；Z：`missing origin SRC-999` | A 跳过 ID 索引、重复检查和前缀检查。第二轮只遍历索引，A 自己的 `origin: SRC-998` 未检查。B、Z 的来源检查均执行并报错。 |
| 7 | 新 | 完成，无异常，`FAIL: 3 YAML records; 4 errors` | A `[id]`：`{'bad': 'SRC-001'} is not of type 'string'`；A：`missing origin SRC-998`；B：`missing origin SRC-001`；Z：`missing origin SRC-999` | A 跳过 ID 索引、重复检查和前缀检查，但仍在第二轮的记录列表，其自身来源检查执行并报错。B、Z 的来源检查均执行并报错。 |

两版均在第一轮按路径排序读取 YAML、收集 Schema 诊断，然后检查跨记录引用。CLI 在 `validate_path` 返回后才打印已收集的诊断和摘要。这解释了批次 2、3、6 的旧版输出中为何没有已收集的 Schema 错误。旧版见 `source/old/scripts/validate_truth.py:47–93,95–105`，新版见 `source/new/scripts/validate_truth.py:47–103,105–115`。

## 1. 批次 1 的历史缺来源判断

可沿用到目标新版的同一条件。校验目录中只有 `REQ-004.yaml`，记录通过 Schema，`origin: SRC-999` 是符合格式的字符串，批次索引没有这个 ID，且流程到达来源检查。两版均将该文件报告为 `missing origin SRC-999`，并以一条诊断正常结束。这个结论限于批次内 ID 是否存在，来源记录的种类、证据充分性与位置有效性各有单独条件。依据为历史材料 H4、`evidence.json` 批次 1 两版、旧版 `examples/invalid/dangling-reference.yaml:1–8`、两版 `schemas/knowledge.schema.json:45–48,81–98`、旧版 `scripts/validate_truth.py:72–80`、新版同路径第 78–87 行及 `specifications/source-of-truth.md:5`。

## 2. 批次 2 的版本交接预期

保留旧版 traceback 为基线记录，并把目标新版的预期更新为两条文件诊断及正常的失败摘要。具体条件是该批 A 有非空字符串 `relations: REQ-002`，排序在拥有悬空 `origin: SRC-999` 的 Z 前面。旧版先收集 Schema 错误，后在 A 上按映射调用 `.items()` 中止。新版保留 A 的 Schema 诊断，跳过取决于 `relations` 类型的遍历，继续报告 Z。若交接需要编写断言，应校验摘要及两条诊断，两个版本共有的退出码 1 无法区分这两种结果。该版本边界仅有这两个快照的证据。依据为历史材料 H1、H2、H3，`evidence.json` 批次 2 两版，旧版 `scripts/validate_truth.py:60–61,72–93,101–105`，新版同路径第 62–64、78–91、111–115 行，以及新版 `tests/test_validation.py:61–69,75–78`。

## 3. 批次 3 与 4 的来源诊断

- **批次 3 旧版。** A 的 `kind: [source]` 违反枚举。第一轮登记字符串 ID `SRC-001` 后，列表参与字典键成员检查时抛出 `TypeError`。登记动作本身只说明进入内部索引。B 的来源解析和 Z 的独立来源检查都未运行，CLI 也没有输出 A 的 Schema 错误。依据为 `evidence.json` 批次 3 旧版和旧版 `scripts/validate_truth.py:54–80,101–105`。
- **批次 3 新版。** A 的 `kind` 仍报 Schema 错误。A 有可入索引的字符串 ID，索引将其种类记录为 `None`。B 查找字符串 `SRC-001` 命中，所以没有 `missing origin`。因种类未知，新版也不报 `origin must be source`。因此 B 的查找结果只说明 ID 存在，整体记录仍有 Schema 错误，且有效 `source` 的规范要求仍适用。Z 的悬空来源独立报告。依据为 `evidence.json` 批次 3 新版、新版 `scripts/validate_truth.py:62–87`、`tests/test_validation.py:61–73` 和 `specifications/source-of-truth.md:5`。
- **批次 4 两版。** 删除 A 后，B 引用的 `SRC-001` 缺席，Z 的 `SRC-999` 仍缺席，两项检查均执行并报错。B 的标题和陈述提到缺验收条件，但输入确有满足 Schema 的 `acceptance`，两版都没有验收字段诊断。依据为 `evidence.json` 批次 3 和 4 的输入及批次 4 两版输出、两版 `schemas/knowledge.schema.json:53–60,81–98`、旧版 `scripts/validate_truth.py:72–80` 与新版同路径第 78–87 行。

## 4. 空列表和非空列表的适用条件

草稿中“任意列表都会崩溃”的范围应改为旧版第二轮实际遍历到该记录时，非空列表触发 `AttributeError`。旧版通过 `(record.get('relations') or {}).items()` 处理空列表，`[]` 的假值使它走空字典分支，Schema 错误仍保留，Z 也继续得到诊断。非空列表保留原值，调用 `.items()` 时崩溃，A 的 Schema 诊断无法打印，Z 的检查未到达。历史 H2 的非空列表示例与该条件相符。若记录因非字符串 ID 被旧版排除在索引外，或批次更早中止，也不会到达该记录的关系遍历。依据为历史材料 H1、H2，`evidence.json` 批次 5、6 旧版，以及旧版 `scripts/validate_truth.py:60–91,101–105`。

新版用字典类型守卫跳过两种列表的关系遍历，两种列表依然违反 Schema，均会报告 A 和 Z。批次 5 的对外结果一致，依赖批次 6 的异常、缺失的独立诊断或空 stdout 的预期须按版本分开。批次 2 的非空字符串也有此版本差异。新版的来源检查位于关系守卫之前，源码与新版单测支持同一记录的独立来源检查仍可执行。依据为 `evidence.json` 批次 2、5、6 两版、两版 `schemas/knowledge.schema.json:62–79`、新版 `scripts/validate_truth.py:78–93`、新版 `tests/test_validation.py:75–87`。

## 5. 非字符串 ID 与维护建议

历史 H2 中“`id` 为映射时正常报告 Schema 错误”在批次 7 的两版均成立。A 的映射值包含文本 `SRC-001`，但两版都要求实际的 `id` 值是字符串才登记，故 B 报 `missing origin SRC-001`。旧版把索引也用作第二轮遍历对象，A 自身的 `origin: SRC-998` 随记录被跳过。新版在类型判断前保留已解析的 A 供第二轮遍历，新增了 A 的独立缺来源诊断。Z 的诊断两版均保留。依据为 `evidence.json` 批次 7 两版、两版 `schemas/knowledge.schema.json:15–18`、旧版 `scripts/validate_truth.py:60–80`、新版同路径第 62–91 行及新版 `tests/test_validation.py:90–92`。

**维护建议（候选，待维护者确认）。** 用批次 7 的输入固定交接断言，条件是记录可解析为映射、其 `id` 为映射、自身的字符串 `origin` 找不到目标，且同批没有其他记录以字符串 ID 登记 `SRC-001` 或 `SRC-999`。在 `9c38156` 预期三条诊断，在 `83a2120` 预期四条，新增项是 A 的 `missing origin SRC-998`。两版均应保留 A 的 `id` 诊断、B 和 Z 各自的缺来源诊断及正常的失败摘要。版本行为已复跑，建议的交接断言尚无相应授权记录。依据为 `evidence.json` 批次 7 两版、上述索引与遍历代码、新版 `tests/test_validation.py:90–92` 和 `specifications/source-of-truth.md:7–9`。

## 核验范围与限制

只使用了分配包内的历史摘录、七批输入及 CLI 记录、两版源码、Schema、规范和测试。用指定的 Python 3.12 及已安装的 PyYAML、jsonschema 在临时目录逐批复跑。仅归一化 traceback 中脚本文件的路径，十四次运行的退出码和两路输出均与记录一致。另运行快照自带测试，旧版 5 项、新版 10 项均通过。输入和快照未改动，未使用包外的项目材料或网络。

材料未包含历史 H2 的完整原始夹具与原始运行环境、中间提交或发布标签，也未附 H3 或本建议获正式确认的授权记录。因此复核能确认给定输入和两个提交上的行为，无法确定历史实验的所有夹具细节、首次修复的提交或正式采纳状态。
