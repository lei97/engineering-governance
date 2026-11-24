# Kubernetes Job 交接材料

以下按来源保留状态字段、运行记录与实现边界。GitHub 议题中的叙述属于报告人或复现者的陈述。上游 Kubernetes 提交与发行商的集群构建分别标识。

## H1 · 2024 年的 Job 终态问题

#123775 的复现使用 Indexed Job、`completions: 4`、`parallelism: 4`、`backoffLimit: 0`、`podReplacementPolicy: Failed`，然后删除一个 Pod。3 月 7 日评论按同一 Job 配置贴出状态。 [议题](https://github.com/kubernetes/kubernetes/issues/123775) · [状态评论](https://github.com/kubernetes/kubernetes/issues/123775#issuecomment-1982959351)

| 2024-03-07 状态字段 | 值 |
| --- | --- |
| `conditions` | `Failed=True`，`BackoffLimitExceeded` |
| `failed` / `ready` / `terminating` | `4` / `2` / `1` |
| `uncountedTerminatedPods` | `{}` |

5 月 16 日，维护者在另一次复现中使用 600 个索引、`backoffLimit: 0`，第 0 个 Pod 先失败。评论保留了以下时间点。 [复现时间轴](https://github.com/kubernetes/kubernetes/issues/123775#issuecomment-2114710754)

| 评论记录的时间 | 观测 |
| --- | --- |
| `11:13:10.933897` | 第 0 个 Pod 失败 |
| `11:13:11.942719` | Job 更新了 `uncountedTerminatedPods` |
| `11:13:23.981958` | Job 出现 `Failed` |
| `11:13:50.139687` | 最后一个 Pod 被标为 `Failed` |

讨论提到 Kueue 看见 Job 失败后可能启动替代任务，当原 Pod 还在消耗资源时会影响配额和调度。 [容量核算讨论](https://github.com/kubernetes/kubernetes/issues/123775#issuecomment-1983329580)

## H2 · 终态发布规则

上游 `v1.30.0` 的 `enactJobFinished` 检查 `uncountedTerminatedPods`，随后可以写入终态条件。2024 年 7 月合并的 #125510 解决 #123775，扩展了 `FailureTarget` 和 `SuccessCriteriaMet` 的用途，让控制器可在终态前公布成败判据的结果。 `v1.31.9` 的延后分支由 `JobManagedBy` 或 `JobPodReplacementPolicy` 任一启用触发。 [v1.30.0 控制器](https://github.com/kubernetes/kubernetes/blob/7c48c2bd72b9bf5c44d21d7338cc7bea77d0ad2a/pkg/controller/job/job_controller.go#L1350-L1369) · [#125510 变更](https://github.com/kubernetes/kubernetes/pull/125510) · [v1.31.9 控制器](https://github.com/kubernetes/kubernetes/blob/8f3800390d488f54f74111f22973059e133f9cba/pkg/controller/job/job_controller.go#L999-L1002)

`v1.32.7` 的内置控制器先检查 `UncountedTerminatedPods` 的成功和失败 UID 数。计数大于零时 `enactJobFinished` 返回 `false`。若启用延后分支，内部终止中 Pod 数大于零也会退出，两个检查均在写入终态之前。API 将 `uncountedTerminatedPods` 定义为已终止且尚未计入 Job 状态计数的 Pod UID。 [v1.32.7 控制器门控](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/pkg/controller/job/job_controller.go#L1082-L1086) · [完成分支](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/pkg/controller/job/job_controller.go#L1476-L1501) · [API 字段](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/staging/src/k8s.io/api/batch/v1/types.go#L602-L614)

API 的 `terminating` 计数涵盖带删除时间戳且仍处于 `Pending` 或 `Running` 的 Pod。`uncountedTerminatedPods` 字段说明的记账步骤依次为登记 UID、移除跟踪 finalizer、从集合移除 UID 并累计计数。 [终止中计数](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/staging/src/k8s.io/api/batch/v1/types.go#L546-L552) · [记账步骤](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/staging/src/k8s.io/api/batch/v1/types.go#L579-L594)

同一版本的普通完成计数路径调用 `newSuccessCondition`，在延后分支开启时可产生 `SuccessCriteriaMet`。启用 `JobSuccessPolicy` 门控时，该路径用 `CompletionsReached`。匹配显式 `spec.successPolicy` 的分支使用另一原因 `SuccessPolicy`。 [策略匹配分支](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/pkg/controller/job/job_controller.go#L965-L969) · [普通完成判据](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/pkg/controller/job/job_controller.go#L993-L1012) · [条件和原因](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/pkg/controller/job/job_controller.go#L1069-L1079)

## H3 · 零完成数、暂停的 Job

#132144 的报告给出 `spec.completions: 0`、`spec.suspend: true`。报告人说明 `v1.31.9` 的输出有 `SuccessCriteriaMet=True`、`Complete=True` 和 `completionTime`，表格为 `Complete`。`v1.32.0+k3s1` 的表格显示 `AGE=2s` 和 `STATUS=Running`，所贴状态片段只有 `SuccessCriteriaMet=True`。早期评论怀疑仍有 Pod 正在终止。 [原报告](https://github.com/kubernetes/kubernetes/issues/132144) · [早期假设](https://github.com/kubernetes/kubernetes/issues/132144#issuecomment-2954740579)

另一位复现者记录两版都未创建 Pod。其 `v1.32` 复现在约 10 分钟的表格仍显示 `Running`，控制器日志包含 `status.startTime: Required value: startTime is required for finished job`。报告人的 Flux 工作流因此没有继续到依赖的下一项。 [独立复现与日志](https://github.com/kubernetes/kubernetes/issues/132144#issuecomment-2957408192) · [用户工作流](https://github.com/kubernetes/kubernetes/issues/132144#issuecomment-2966466616)

| 上游默认门控 | `v1.31.9` | `v1.32.0` |
| --- | --- | --- |
| `JobManagedBy` | `false`，Alpha | `true`，Beta |
| `JobPodReplacementPolicy` | `true`，Beta | `true`，Beta |

门控默认值取自发行提交。 [1.31.9 门控](https://github.com/kubernetes/kubernetes/blob/8f3800390d488f54f74111f22973059e133f9cba/pkg/features/kube_features.go#L1094-L1100) · [1.32.0 门控](https://github.com/kubernetes/kubernetes/blob/70d3cc986aa8221cd1dfb1121852688902d3bf53/pkg/features/versioned_kube_features.go#L430-L444)

两提交的 `pkg/registry/batch/job/strategy.go` 对应 blob `1de03e459da69e59a734413a0348b2c033995334`。该文件的 `getStatusValidationOptions` 中，增强校验选项的代码块受 `JobManagedBy` 控制。块内的 `RejectFinishedJobWithoutStartTime` 取 `isJobFinishedChanged || isStartTimeChanged`。 [1.31.9 状态策略](https://github.com/kubernetes/kubernetes/blob/8f3800390d488f54f74111f22973059e133f9cba/pkg/registry/batch/job/strategy.go#L344-L405) · [1.32.0 状态策略](https://github.com/kubernetes/kubernetes/blob/70d3cc986aa8221cd1dfb1121852688902d3bf53/pkg/registry/batch/job/strategy.go#L344-L405)

`v1.32.0` 的 `validateJobStatus` 在该选项生效、`StartTime == nil` 且拟更新状态为终态时，对 `startTime` 返回 Required 错误。`printJob` 的最终 `else` 分支写 `Running`。 [状态校验](https://github.com/kubernetes/kubernetes/blob/70d3cc986aa8221cd1dfb1121852688902d3bf53/pkg/apis/batch/validation/validation.go#L530-L539) · [Job 表格输出](https://github.com/kubernetes/kubernetes/blob/70d3cc986aa8221cd1dfb1121852688902d3bf53/pkg/printers/internalversion/printers.go#L1209-L1226)

## H4 · 回归修复

合并的 #132614 与回移到 `release-1.32` 的 #132727 在 `suspend=true` **且** `completions=0` 时，不启用该项缺 `startTime` 的拒绝检查。修复加入了验证该配置能出现 `SuccessCriteriaMet` 和 `Complete` 的集成用例。维护者报告在 kind 集群用原配置观察到 `Complete`。原报告人后来确认 `1.32.7` 和 `1.33.3` 解决其回归。 [主线修复](https://github.com/kubernetes/kubernetes/pull/132614) · [回移](https://github.com/kubernetes/kubernetes/pull/132727) · [v1.32.7 源码](https://github.com/kubernetes/kubernetes/blob/158eee9fac884b429a92465edd0d88a43f81de34/pkg/registry/batch/job/strategy.go#L377-L400) · [kind 观察](https://github.com/kubernetes/kubernetes/issues/132144#issuecomment-3036731203) · [报告人确认](https://github.com/kubernetes/kubernetes/issues/132144#issuecomment-3088832393)

## T1 · 2025 年 9 月的 EKS Helm Hook 报告

#133903 的提交者报告 Helm pre-install/pre-upgrade Hook Job 没进入 `Complete`，后续 Deployment 未创建。服务器版本报告为 `v1.32.7-eks-ace6451`。给出的复现片段使用 `restartPolicy: Never`、`backoffLimit: 2`，未展示 `successPolicy`、`suspend: true` 或 `completions: 0`。以下是原报告给出的 Job 状态值。 [原报告和配置片段](https://github.com/kubernetes/kubernetes/issues/133903)

| 字段 | 值 |
| --- | --- |
| 条件及原因 | `SuccessCriteriaMet=True`，`CompletionsReached` |
| `lastTransitionTime` | `2025-09-05T06:10:23Z` |
| `startTime` | `2025-09-05T06:10:09Z` |
| `terminating` | `0` |
| `uncountedTerminatedPods.succeeded` | 一条 UID `ccbd79bb-77f2-44d5-b460-34a06d87fc26` |
| `Complete` | 此状态片段未显示 |

## T2 · EKS 报告的关闭说明

原报告人在关闭前将问题归因于一个持续修改 Pod 的 Kyverno 策略，并称这阻碍了终止中 Pod 的删除。 [报告人关闭说明](https://github.com/kubernetes/kubernetes/issues/133903#issuecomment-3285025422)
