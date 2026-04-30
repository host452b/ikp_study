# IKP 数据目录

本目录保存论文中使用的探针集、每个模型的原始答案及衍生汇总。

## 核心产物（论文使用）

| 文件 | 用途 |
|---|---|
| `probes/final_probe_set_v8.json` | **IKP 基准的 1,400 个探针。** 200 题 × 7 层级（T1–T7）。 |
| `results/<model>.json` | 逐模型评测输出（168 个文件），包含逐层级准确率、幻觉率及逐探针评测结果。 |
| `results/evaluation_summary.json` | 所有模型的聚合汇总，供所有图表脚本消费。 |
| `calibration/calibration_fit.json` | 拟合的对数线性校准（斜率、截距、R²、N）。 |
| `researcher_citations.json` | T4–T7 中使用的每位研究者实体的引用数 + h 指数。 |
| `researcher_recognition_rates.json` | 每位研究者在所有模型中的识别率。 |
| `densing_analysis_data.csv` | Densing 定律证伪图的数据表。 |

## 探针模式（`probes/final_probe_set_v8.json`）

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

## 逐模型结果模式（`results/<model>.json`）

```json
{
  "model_id": "openai/gpt-4.1",
  "accuracy": 0.62,           // 惩罚性
  "raw_accuracy": 0.68,
  "tier_accuracy": {"T1": 0.99, …, "T7": 0.03},
  "probe_results": [
    {"id":"IKP_T1_0000", "verdict":"CORRECT"}
  ]
}
```

评测结果取值为 `CORRECT`、`WRONG`、`REFUSAL` 之一。惩罚性准确率 = `(correct − 0.5·wrong) / total`。

## 目录结构

```
data/
├── probes/
│   ├── final_probe_set_v8.json   ← 1,400 个探针（基准测试）
│   └── archive/                  ← 早期探针迭代版本
├── results/                      ← 逐模型评测结果
├── calibration/                  ← 拟合的对数线性校准
├── researcher_citations.json
├── researcher_recognition_rates.json
├── densing_analysis_data.csv
├── notes/                        ← 探索性分析 Markdown（论文未引用）
└── archive/                      ← 已废弃的数据快照
```

## 复现时可忽略的目录

`api_cache/`、`raw_responses/`、`backups/`、`archive/`、`probes/archive/`、`notes/*.md` 均不被论文图表脚本读取，可安全忽略。
