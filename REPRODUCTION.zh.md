# 复现论文中的每张图表

> 本文件为 [`ikp/REPRODUCTION.md`](ikp/REPRODUCTION.md) 的中文翻译，
> 适用于在 `ikp/` 子模块内执行的命令。
> 从 `ikp_study/` 根目录运行时，所有命令路径须加 `ikp/` 前缀。

## 0. 一键重建

```bash
cd ikp   # 进入子模块目录
pip install -r requirements.txt

python paper/figures/generate_figures.py             # 图 1–6、8
python paper/figures/generate_appendix_figures.py    # 图 A1–A4
python scripts/loo_cv_analysis.py                    # 图 7
python scripts/14_comprehensive_fingerprinting.py    # 图 9 + 指纹表格
python scripts/15_densing_law_analysis.py            # Densing CSV + 附录统计

latexmk -pdf paper/main.tex
```

## 1. 输入文件

| 产物 | 由谁生成 | 由谁读取 |
|---|---|---|
| `data/probes/final_probe_set_v8.json` | `01_generate_probes.py` 等 | 所有评测器 |
| `data/results/<model>.json`（×188） | `run_all_models.py` | `evaluation_summary.json` 构建器 |
| `data/results/evaluation_summary.json` | `run_evaluation.py` | 每个图表脚本 |
| `configs/all_models.json` | 手动 / `add_release_dates.py` | 需要元数据的脚本 |
| `data/researcher_citations.json` | `09_researcher_probes.py` | 图 5、表 3–4 |
| `data/densing_analysis_data.csv` | `15_densing_law_analysis.py` | 图 8 |

## 2. 正文图表

| 标签 | 生成函数 | 内容 |
|---|---|---|
| 图 1 `fig:calibration` | `fig1_calibration()` | 89 个开源模型的 IKP 对数线性校准曲线（R² = 0.917） |
| 图 2 `fig:heatmap` | `fig2_tier_heatmap()` | 逐层级准确率热力图，前 25 个模型 |
| 图 3 `fig:thinking` | `fig3_thinking_effect()` | `-think` vs 基础版的逐对 Δ 准确率 |
| 图 4 `fig:moe` | `fig4_moe_params()` | MoE 总参数 vs 活跃参数拟合（R² 0.79 vs 0.51） |
| 图 5 `fig:researcher` | `fig5_researcher_scatter()` | 识别率 vs 对数引用数（Spearman ρ = 0.575） |
| 图 6 `fig:fingerprint` | `fig6_fingerprint_heatmap()` | T5–T6 幻觉相似度 Jaccard 热力图 |
| 图 7 `fig:loo` | `loo_cv_analysis.py` | 留一法交叉验证 |
| 图 8 `fig:densing` | `fig8_densing_law()` | IKP 残差随时间变化——驳斥 Densing 定律 |
| 图 9 `fig:lineage` | `14_comprehensive_fingerprinting.py` | 各模型家族 HSS vs Jaccard 轨迹 |

## 3. 附录图表

| 标签 | 函数 |
|---|---|
| 图 A1 | `fig_a1_tier_boxplots()` |
| 图 A2 | `fig_a2_vendor_hallucination()` |
| 图 A3 | `fig_a3_generation_trajectories()` |
| 图 A4 | `fig_a4_gpt5_family()` |

## 4. 从头完整重跑

```bash
cd ikp

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
latexmk -pdf paper/main.tex
```

## 5. 故障排除

- **`evaluation_summary.json` 已过时** → `python scripts/run_evaluation.py --rebuild-summary`
- **图 6 / 图 9 报 "KeyError"** → 配置中有模型但结果文件不存在，补跑或删除配置条目
- **Densing 图不对** → 重新运行 `scripts/15_densing_law_analysis.py`
- **裁判结果不一致** → 若 `google/gemini-3-flash-preview` 被弃用，编辑 `JUDGE_MODEL` 并重新校准
