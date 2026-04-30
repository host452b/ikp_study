# 不可压缩知识探针（IKP）

论文评测工具包与复现包：

> **不可压缩知识探针：通过事实能力估计黑盒 LLM 的参数量。** Bojie Li，Pine AI。

IKP 是一个包含 1,400 道题的事实性基准测试——200 题 × 7 个难度层级（T1：通识知识 … T7：极长尾知识）。在 89 个参数量从 1.35 亿到 1.6 万亿的开源模型上，IKP 准确率与参数量呈**对数线性关系**（R² = 0.917），因此只需一次黑盒 API 调用，即可估算任意已部署模型（包括未公开参数量的闭源前沿模型）的有效知识容量。

- **论文 PDF：** `paper/main.pdf`
- **配套网站（交互式）：** https://01.me/research/ikp
- **源代码：** https://github.com/19PINE-AI/ikp

## 快速开始——估计模型参数量

```bash
# 1. 安装依赖（Python ≥ 3.10）
pip install -r requirements.txt

# 2. 指向任意 OpenAI 兼容端点并运行
export OPENROUTER_API_KEY=sk-or-...
python scripts/ikp_estimate.py --model openai/gpt-4.1
```

输出：

```
  ╔══════════════════════════════════════════════════════════╗
  ║  IKP Estimation Results                                 ║
  ║  Model:     openai/gpt-4.1                              ║
  ║  Probes:    1400                                         ║
  ║  Accuracy:  58.2% (penalized)  63.9% (raw)              ║
  ║  Estimated:  400B parameters                             ║
  ╚══════════════════════════════════════════════════════════╝
  T1   99%  …  T7    4%
  Effective tier: T6
  Estimated size: 400B (calibrated on 89 open models, R²=0.917)
```

更快的分层采样（200 道题，约 1 分钟）：

```bash
python scripts/ikp_estimate.py --model openai/gpt-4.1 --sample 200
```

非 OpenRouter 端点（vLLM、OpenAI、Together、本地）：

```bash
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  <your-key> \
    --model    my-local-model
# 裁判模型始终在 OpenRouter 上运行（google/gemini-3-flash-preview）；
# 仍需设置 OPENROUTER_API_KEY 供裁判使用。
```

完整 CLI 参考（包括接入自定义裁判或导出逐题评测结果），请见 [`TOOLKIT.zh.md`](TOOLKIT.zh.md)。

## 交互式 CLI——探索基准测试

第二个轻量 CLI（`python -m cli`）允许读者在不运行完整估算器的情况下探索基准测试。提供两种模式。

**研究模式**——使用研究者姓名或任意事实性问题，查询六个层级地标模型及三个前沿模型（GPT-5.5、DeepSeek V4 Pro、Claude Opus 4.7）的回答：

```bash
export OPENROUTER_API_KEY=sk-or-...

# 查找研究者（对探针集做子字符串匹配）
python -m cli research --researcher "Stjepan Picek"

# 提问任意事实性问题
python -m cli research --question "Who founded the field of cache-oblivious algorithms?"
```

**评测模式**——用预设模型（及您自定义的模型）重新运行任意探针，使用论文完全相同的裁判提示（`google/gemini-3-flash-preview`，CORRECT / WRONG / REFUSAL）：

```bash
# 用预设 9 个模型评分单个 T7 探针
python -m cli eval IKP_T7_1234

# 添加自定义模型；--model 可重复使用
python -m cli eval IKP_T5_0123 \
    --model openai/gpt-4o \
    --model id=qwen/qwen3-32b,name=q3-32b,thinking=true
```

T1 使用本地 Ollama 地标（`qwen2.5:0.5b`）；安装 Ollama 或忽略该行。其余八个模型均通过 OpenRouter 运行。

## 复现论文

论文中每张图表对应的脚本、输入和预期输出均在 [`REPRODUCTION.zh.md`](REPRODUCTION.zh.md) 中列出。

快速路径：

```bash
# 最快：直接从已评分结果重新生成所有图表
python paper/figures/generate_figures.py
python paper/figures/generate_appendix_figures.py

# 重编译 PDF（需 TeX Live）
cd paper && latexmk -pdf main.tex
```

评分更多模型并扩展数据集：

```bash
python scripts/run_all_models.py --skip-existing
python scripts/run_evaluation.py --rebuild-summary  # 刷新 evaluation_summary.json
```

## 构建论文 / 网站

`Makefile` 是唯一的入口点。

```bash
make help              # 列出所有目标

# 论文
make figs              # 重新生成 paper/figures/ 下的所有图表
make pdf               # 单次 pdflatex（快速，不含 bibtex）
make full              # 完整重编译（含 bibtex，共 4 次）

# 新模型加入 data/results/ 后，刷新校准数据
make calibration       # 重新运行 loo_cv_analysis.py + analyze_results.py
make website           # 重建 website/public/data/*.json（website-build 前须先运行）
make data              # = calibration + website

# 网站
make website-dev       # vite 开发服务器 → http://localhost:5173
make website-build     # 静态构建 → website/dist/
make website-preview   # 预览生产构建
make website-deploy    # 通过 rsync 将 website/dist/ 部署到 DEPLOY_HOST:DEPLOY_PATH

make all               # data → figs → pdf
```

## 仓库结构

```
ikp/
├── README.md / README.zh.md        ← 主说明（英文 / 中文）
├── TOOLKIT.md / TOOLKIT.zh.md      ← CLI 参考
├── REPRODUCTION.md / .zh.md        ← 图表复现指南
├── PROJECT_ANALYSIS.md / .zh.md    ← 项目深度解析（双语）
├── requirements.txt
│
├── paper/          ← LaTeX 源码 + 图表生成器
├── configs/        ← 层级定义、模型名单
├── data/           ← 1,400 个探针、188 个模型评测结果
├── scripts/        ← 估算器、流水线、分析脚本
├── src/            ← 评测运行时
├── cli/            ← 交互式 CLI
└── website/        ← React 配套网站
```

## 工作原理（一段话）

每个探针是一道简短的事实性问题，配有标准答案，由 Gemini 3 Flash Preview 裁判评分。惩罚性准确率对错误答案扣 −1.0 分以阻止猜测。校准曲线为 `log10(params_B) = 6.790 · accuracy − 0.899`（R² = 0.917，89 个开源模型；LOO 中位数折叠误差 1.59×）。对于 MoE 模型，**总**参数量比活跃参数量更好地预测准确率（R² = 0.79 对 0.51）。

## 环境要求

- Python ≥ 3.10
- 待评估模型的 API 密钥（OpenRouter 覆盖所有 188 个评估模型）
- 裁判所需的 `OPENROUTER_API_KEY`（始终使用 Gemini 3 Flash Preview）
- 每个模型评分 1,400 个探针的成本约 $0.10–$3

## 引用

```bibtex
@misc{li2026ikp,
  title  = {Incompressible Knowledge Probes: Estimating Black-Box LLM
            Parameter Counts via Factual Capacity},
  author = {Bojie Li},
  year   = {2026},
  note   = {Pine AI. \url{https://01.me/research/ikp}}
}
```

## 许可证

代码：MIT。探针集及各模型结果：CC BY 4.0。
