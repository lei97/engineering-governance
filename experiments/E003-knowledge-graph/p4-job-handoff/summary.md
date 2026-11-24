# 历史交接摘要

- **J1** Job 终态发布早于最后一个 Pod 的终态记录。范围：H1 的 2024-05-16 复现，Job 终态为 Failed，具体构建未给出。状态：历史观测。证据：H1 · 5 月时间轴。
- **J2** Job 终态发布受限于终态延后分支。范围：上游 v1.31.9 与 v1.32.7 的内置控制器，JobManagedBy 或 JobPodReplacementPolicy 任一启用且仍有终止中 Pod 时延后。状态：固定版本源码。证据：H2 · 两个门控函数与完成分支。
- **J3** SuccessCriteriaMet可先于Job 终态发布。范围：#125510 扩展后的内置控制器，提前公布成功判据；失败时对应的提前条件是 FailureTarget。状态：已合并变更。证据：H2 · #125510 发布说明。
- **J4** 非空 uncountedTerminatedPods阻止Job 终态发布。范围：上游 v1.32.7 内置控制器执行 enactJobFinished，成功或失败 UID 计数大于零。状态：固定版本源码。证据：H2 · 完成分支与 API 字段。
- **J5** JobManagedBy控制增强的 Job 状态校验。范围：上游 v1.32.0 的默认值是启用，v1.31.9 是禁用，JobPodReplacementPolicy 两版均默认启用。状态：固定版本源码。证据：H3 · 门控定义和状态校验选项。
- **J6** 增强的 Job 状态校验可拒绝Job 终态发布。范围：上游 v1.32.0，JobManagedBy 启用，进入终态或 startTime 发生变化，拟更新状态为终态且 StartTime 为 nil，触发 RejectFinishedJobWithoutStartTime 检查。状态：固定版本源码。证据：H3 · 状态校验选项和拒绝条件。
- **J7** 早期评论者怀疑Pod 仍在终止导致 Running。范围：#132144 的首次约 2 秒状态片段。状态：历史假设。证据：H3 · 早期评论。
- **J8** v1.32 的独立复现记录无 Pod 且终态更新因缺 startTime 被拒。范围：#132144 的暂停、零完成数 Job，约 10 分钟仍显示 Running。状态：历史复现日志。证据：H3 · 独立复现及日志。
- **J9** 上游 v1.32.7 的回移修复限定增强的 Job 状态校验。范围：suspend=true 且 completions=0 时，豁免缺 startTime 的终态更新检查。状态：已合并变更。证据：H4 · #132727 与固定源码。
- **J10** 普通完成计数路径可以产生SuccessCriteriaMet。范围：上游 v1.32.7 内置控制器，延后分支和 JobSuccessPolicy 门控开启，此时原因是 CompletionsReached；匹配显式 successPolicy 的分支使用 SuccessPolicy 原因。状态：固定版本源码。证据：H2 · 普通完成条件和策略匹配分支。
