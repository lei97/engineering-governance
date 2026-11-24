# 历史交接关系图

边从源节点指向目标节点。

| 节点 | 含义 |
| --- | --- |
| N1 | Job 终态发布 |
| N2 | 最后一个 Pod 的终态记录 |
| N3 | 终态延后分支 |
| N4 | SuccessCriteriaMet |
| N5 | 非空 uncountedTerminatedPods |
| N6 | JobManagedBy |
| N7 | 增强的 Job 状态校验 |
| N8 | 早期评论者 |
| N9 | Pod 仍在终止导致 Running |
| N10 | v1.32 的独立复现 |
| N11 | 无 Pod 且终态更新因缺 startTime 被拒 |
| N12 | 上游 v1.32.7 的回移修复 |
| N13 | 普通完成计数路径 |

| ID | 源 | 关系 | 目标 | 范围 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| J1 | N1 | 早于 | N2 | H1 的 2024-05-16 复现，Job 终态为 Failed，具体构建未给出 | 历史观测 | H1 · 5 月时间轴 |
| J2 | N1 | 受限于 | N3 | 上游 v1.31.9 与 v1.32.7 的内置控制器，JobManagedBy 或 JobPodReplacementPolicy 任一启用且仍有终止中 Pod 时延后 | 固定版本源码 | H2 · 两个门控函数与完成分支 |
| J3 | N4 | 可先于 | N1 | #125510 扩展后的内置控制器，提前公布成功判据；失败时对应的提前条件是 FailureTarget | 已合并变更 | H2 · #125510 发布说明 |
| J4 | N5 | 阻止 | N1 | 上游 v1.32.7 内置控制器执行 enactJobFinished，成功或失败 UID 计数大于零 | 固定版本源码 | H2 · 完成分支与 API 字段 |
| J5 | N6 | 控制 | N7 | 上游 v1.32.0 的默认值是启用，v1.31.9 是禁用，JobPodReplacementPolicy 两版均默认启用 | 固定版本源码 | H3 · 门控定义和状态校验选项 |
| J6 | N7 | 可拒绝 | N1 | 上游 v1.32.0，JobManagedBy 启用，进入终态或 startTime 发生变化，拟更新状态为终态且 StartTime 为 nil，触发 RejectFinishedJobWithoutStartTime 检查 | 固定版本源码 | H3 · 状态校验选项和拒绝条件 |
| J7 | N8 | 怀疑 | N9 | #132144 的首次约 2 秒状态片段 | 历史假设 | H3 · 早期评论 |
| J8 | N10 | 记录 | N11 | #132144 的暂停、零完成数 Job，约 10 分钟仍显示 Running | 历史复现日志 | H3 · 独立复现及日志 |
| J9 | N12 | 限定 | N7 | suspend=true 且 completions=0 时，豁免缺 startTime 的终态更新检查 | 已合并变更 | H4 · #132727 与固定源码 |
| J10 | N13 | 可以产生 | N4 | 上游 v1.32.7 内置控制器，延后分支和 JobSuccessPolicy 门控开启，此时原因是 CompletionsReached；匹配显式 successPolicy 的分支使用 SuccessPolicy 原因 | 固定版本源码 | H2 · 普通完成条件和策略匹配分支 |
