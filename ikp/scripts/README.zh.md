# scripts/ 目录

## 公开入口——推荐使用

| 脚本 | 用途 |
|---|---|
| `ikp_estimate.py` | 对单个模型在 1,400 个探针集上评分，打印估算的参数量。详见 `../TOOLKIT.zh.md`。 |
| `run_all_models.py` | 批量评分 `configs/all_models.json` 中的所有模型（幂等、可恢复）。 |
| `run_evaluation.py` | 按名称评分单个模型；由 `run_all_models.py` 调用，也可独立运行。 |

## 数据集流水线（编号，可复现）

| 阶段 | 脚本 | 输出 |
|---|---|---|
| 探针生成（T1–T4） | `01_generate_probes.py`、`01b_generate_t6_t7.py` | 层级候选探针 |
| 校准评测 | `02_run_calibration.py` | 每个校准模型的原始答案 |
| 校准拟合 | `03_fit_calibration.py` | `data/calibration/calibration_fit.json` |
| 目标评测 | `04_run_targets.py` | 每个目标模型的原始答案 |
| 中文探针 | `08_chinese_probes.py` | 中文语言子集 |
| 研究者探针 | `09_researcher_probes.py` | T4–T7 研究者子集 |
| 网络依托 | `10_web_grounded_probes.py` | 基于网络频率的探针 |
| 语料库依托 | `11_corpus_grounded_t5t7.py` | T5–T7 语料库依托探针 |
| 指纹探针 | `12_fingerprint_probes.py` | 附录 §D 的扩展表述子集 |
| 蒸馏检测 | `13_distillation_detection.py` | 早期指纹分析 |
| 指纹分析 | `14_comprehensive_fingerprinting.py` | 图 9 + `results/tables/fp_*.tex` |
| Densing 分析 | `15_densing_law_analysis.py` | `data/densing_analysis_data.csv` |
| 数据集组装 | `assemble_final_dataset.py` | `data/probes/final_probe_set_v8.json` |
| 元数据 | `add_release_dates.py` | 扩充 `configs/all_models.json` |

## 分析 / 事后处理

| 脚本 | 用途 |
|---|---|
| `analyze_results.py` | 聚合逐层级准确率，构建 `evaluation_summary.json`。 |
| `loo_cv_analysis.py` | 留一法交叉验证 + 生成图 7。 |
| `show_progress.py` | 快速文本进度汇总。 |

## legacy/

来自早期数据集迭代的旧版一次性脚本，仅作审计保留，复现论文无需运行。
