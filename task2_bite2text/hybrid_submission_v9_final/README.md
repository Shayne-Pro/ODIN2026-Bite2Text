# Bite2Text v9 final：conservative fact-risk reranking

v9 冻结 v8a.2 的全量 PTv3、口内照模型、检索库、中线纠错和 precision sanitizer，仅在检索决策层增加保守的事实风险重排。

原始 v8a.2 分数仍为：

```text
cosine + 0.5 * PTv3 hard agreement + 0.2 * photo soft agreement
```

仅当原始最高分报告存在高置信结构冲突，且替代报告的原始分数落后不超过 `0.02` 时，才应用风险分数：

```text
original_score - 0.005 * unsupported_sentences - 0.5 * contradiction_risk
```

最终门控还要求：

- 高置信冲突风险至少降低 `0.015`；
- 替代报告不能增加 unsupported sentence 数；
- 其余病例保持 v8a.2 选择不变；
- `BITE2TEXT_RISK_RERANK=0` 可精确回退至 v8a.2。

## 严格五折 OOF（867 例）

官方 evaluator：

| 版本 | BLEU-4 | METEOR | Combined |
|---|---:|---:|---:|
| v8a.2 | 0.267154 | 0.469131 | 0.368143 |
| v9 | 0.268426 | 0.470040 | 0.369233 |
| 增量 | +0.001272 | +0.000909 | +0.001090 |

v9 仅改变 8/867 例，五个 OOF fold 的 Combined 全部提升。

RadFact-Lite/GLM-5.2 对全部 8 个受影响病例的成对评估：

- v8a.2：Precision 0.2973，Recall 0.2364，F1 0.2634；
- v9：Precision 0.3700，Recall 0.3659，F1 0.3680；
- 病例级：7 胜、0 平、1 负，0 个 LLM failure。

## 镜像

镜像标签：`odin2026-bite2text-hybrid-photo-test-v9:latest`。
