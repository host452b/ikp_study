# 复现论文中的每张图表

本文档将 `paper/main.tex` 和 `paper/appendix.tex` 中每个带标签的图表，与生成它的脚本、读取的数据文件及写出的输出路径一一对应。若您已具备 `data/results/` 和 `data/probes/final_probe_set_v8.json`，整篇论文可在几分钟内重建完毕。

## 0. 一键重建

```bash
pip install -r requirements.txt

python paper/figures/generate_figures.py             # 图 1–6、8
python paper/figures/generate_appendix_figures.py    # 图 A1–A4
python scripts/loo_cv_analysis.py                    # 图 7
python scripts/14_comprehensive_fingerprinting.py    # 图 9 + 指纹表格
python scripts/15_densing_law_analysis.py            # Densing CSV + 附录统计

cd paper && latexmk -pdf main.tex
```

## 1. 输入文件

| 产物 | 由谁生成 | 由谁读取 |
|---|---|---|
| `data/probes/final_probe_set_v8.json` | `01_generate_probes.py` 等 | 所有评测器 + `ikp_estimate.py` |
| `data/results/<model>.json`（×188） | `run_all_models.py` → `run_evaluation.py` | `evaluation_summary.json` 构建器 |
| `data/results/evaluation_summary.json` | `run_evaluation.py` | 每个图表脚本 |
| `configs/all_models.json` | 手动 / `add_release_dates.py` | 需要元数据的图表脚本 |
| `data/researcher_citations.json` | `09_researcher_probes.py` | 图 5、表 3–4 |
| `data/densing_analysis_data.csv` | `15_densing_law_analysis.py` | 图 8 + 表 A5–A6 |

## 2. 正文图表

| 标签 | PDF | 生成脚本 | 内容 |
|---|---|---|---|
| 图 1 `fig:calibration` | `fig1_calibration.pdf` | `generate_figures.py::fig1_calibration()` | 89 个开源模型的 IKP 对数线性校准曲线（R² = 0.917） |
| 图 2 `fig:heatmap` | `fig2_tier_heatmap.pdf` | `fig2_tier_heatmap()` | 逐层级准确率热力图，前 25 个模型 |
| 图 3 `fig:thinking` | `fig3_thinking_effect.pdf` | `fig3_thinking_effect()` | `-think` vs 基础版的逐对 Δ 准确率 |
| 图 4 `fig:moe` | `fig4_moe_params.pdf` | `fig4_moe_params()` | MoE 总参数 vs 活跃参数拟合（R² 0.79 vs 0.51） |
| 图 5 `fig:researcher` | `fig5_researcher_citations.pdf` | `fig5_researcher_scatter()` | 识别率 vs 对数引用数（Spearman ρ = 0.575） |
| 图 6 `fig:fingerprint` | `fig6_fingerprint_heatmap.pdf` | `fig6_fingerprint_heatmap()` | T5–T6 幻觉相似度 Jaccard 热力图 |
| 图 7 `fig:loo` | `fig7_loo_validation.pdf` | `loo_cv_analysis.py` | 留一法交叉验证下的预测 vs 真实对数参数量 |
| 图 8 `fig:densing` | `fig8_densing_law.pdf` | `fig8_densing_law()` | IKP 残差随时间变化——驳斥 Densing 定律 |
| 图 9 `fig:lineage` | `fig9_family_lineage.pdf` | `14_comprehensive_fingerprinting.py` | 各模型家族的 HSS vs Jaccard 轨迹 |

## 3. 附录图表

| 标签 | PDF | 函数 |
|---|---|---|
| 图 A1 | `fig_a1_tier_boxplots.pdf` | `fig_a1_tier_boxplots()` |
| 图 A2 | `fig_a2_vendor_hallucination.pdf` | `fig_a2_vendor_hallucination()` |
| 图 A3 | `fig_a3_generation_trajectories.pdf` | `fig_a3_generation_trajectories()` |
| 图 A4 | `fig_a4_gpt5_family.pdf` | `fig_a4_gpt5_family()` |

## 4. 表格

### 脚本生成的 `.tex` 文件

| 标签 | 文件 | 生成脚本 |
|---|---|---|
| 族内指纹汇总（`fp_all_families`） | `results/tables/fp_all_families.tex` | `14_comprehensive_fingerprinting.py` |
| 指纹对照组（`fp_controls`） | `results/tables/fp_controls.tex` | 同上 |
| 跨供应商异常值（`fp_cross_vendor`） | `results/tables/fp_cross_vendor.tex` | 同上 |
| 校准汇总（`table1_calibration`） | `results/tables/table1_calibration.tex` | `loo_cv_analysis.py` |

## 5. 从头完整重跑

```bash
# 1. 重建探针集（可选，已附带冻结版本）
python scripts/01_generate_probes.py
python scripts/01b_generate_t6_t7.py
python scripts/assemble_final_dataset.py

# 2. 校准
python scripts/02_run_calibration.py
python scripts/03_fit_calibration.py

# 3. 对所有模型评分（耗时 24–72 小时，约 $100–$300）
export OPENROUTER_API_KEY=sk-or-...
python scripts/run_all_models.py --skip-existing

# 4. 重建图表和表格
python paper/figures/generate_figures.py
python paper/figures/generate_appendix_figures.py
python scripts/loo_cv_analysis.py
python scripts/14_comprehensive_fingerprinting.py
python scripts/15_densing_law_analysis.py

# 5. 编译
cd paper && latexmk -pdf main.tex
```

## 6. 故障排除

- **`evaluation_summary.json` 已过时** → 运行 `python scripts/run_evaluation.py --rebuild-summary`
- **图 6 / 图 9 报 "KeyError"** → `configs/all_models.json` 中有模型但 `data/results/<model>.json` 不存在，补跑该模型或删除配置条目
- **Densing 图不对** → 重新运行 `scripts/15_densing_law_analysis.py`
- **裁判结果不一致** → 若 `google/gemini-3-flash-preview` 被 OpenRouter 弃用，编辑 `ikp_estimate.py` 和 `src/scorer.py` 中的 `JUDGE_MODEL`，并重新校准
