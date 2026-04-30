# IKP 数据目录（中文说明）

> 本文件为 [`ikp/data/README.md`](../ikp/data/README.md) 的中文翻译。
> 所有数据文件位于 `ikp/data/` 子模块目录下。

## 核心产物（论文使用）

| 文件（相对于 `ikp/`） | 用途 |
|---|---|
| `data/probes/final_probe_set_v8.json` | **IKP 基准的 1,400 个探针。** 200 题 × 7 层级（T1–T7）。 |
| `data/results/<model>.json` | 逐模型评测输出（168 个文件），包含逐层级准确率、幻觉率及逐探针评测结果。 |
| `data/results/evaluation_summary.json` | 所有模型的聚合汇总，供所有图表脚本消费。 |
| `data/calibration/calibration_fit.json` | 拟合的对数线性校准（斜率、截距、R²、N）。 |
| `data/researcher_citations.json` | T4–T7 中使用的每位研究者实体的引用数 + h 指数。 |
| `data/densing_analysis_data.csv` | Densing 定律证伪图的数据表。 |

## 探针模式

```json
{
  "id": "IKP_T3_0042",
  "question": "…",
  "answer": "标准答案（';' 分隔可接受的多个答案）",
  "tier": "T3",
  "source_type": "wikidata | llm | researcher | manual",
  "domain": "geography | scientist | …"
}
```

## 逐模型结果模式

```json
{
  "model_id": "openai/gpt-4.1",
  "accuracy": 0.62,
  "tier_accuracy": {"T1": 0.99, …, "T7": 0.03},
  "probe_results": [{"id":"IKP_T1_0000", "verdict":"CORRECT"}]
}
```

评测结果取值：`CORRECT`、`WRONG`、`REFUSAL`。惩罚性准确率 = `(correct − 0.5·wrong) / total`。
