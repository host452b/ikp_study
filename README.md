# ikp_study

Study repo built on top of [IKP (Incompressible Knowledge Probes)](https://github.com/19PINE-AI/ikp) — a benchmark that estimates black-box LLM parameter counts from factual knowledge capacity.

The upstream project lives in the `ikp/` submodule (read-only). This repo adds Chinese documentation, a bilingual project analysis, and an extended estimator script with `--tiers` filtering for local/quantized model testing.

---

**[中文版说明见下方 ↓](#chinese)**

---

## Quick start

```bash
git clone --recurse-submodules https://github.com/host452b/ikp_study.git
cd ikp_study
pip install -r ikp/requirements.txt
export OPENROUTER_API_KEY=sk-or-...

# Full benchmark (1,400 probes)
python scripts/ikp_estimate.py --model openai/gpt-4.1

# Local/quantized model — hard tiers only
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model my-model --tiers T4,T5,T6,T7
```

## Document map

### This repo (`ikp_study/`)

| Document | Language | Description |
|---|---|---|
| **`README.md`** | EN / ZH | This file — entry point and document guide |
| **`README.zh.md`** | ZH | Chinese overview of ikp_study |
| **`TOOLKIT.md`** | EN | CLI reference for `scripts/ikp_estimate.py` — includes `--tiers` flag and local model testing guide |
| **`TOOLKIT.zh.md`** | ZH | Same in Chinese |
| **`PROJECT_ANALYSIS.md`** | EN | Deep dive: what IKP does, methodology, workflow, key findings, extension ideas |
| **`PROJECT_ANALYSIS.zh.md`** | ZH | Same in Chinese |
| **`REPRODUCTION.zh.md`** | ZH | Paper figure/table reproduction guide in Chinese |
| **`data/README.zh.md`** | ZH | Data directory schema in Chinese |
| **`scripts/README.zh.md`** | ZH | Scripts directory index in Chinese |
| **`website/README.zh.md`** | ZH | Website build and deploy guide in Chinese |

### Upstream submodule (`ikp/`)

| Document | Language | Description |
|---|---|---|
| **`ikp/README.md`** | EN | Upstream project overview and quickstart |
| **`ikp/TOOLKIT.md`** | EN | Upstream CLI reference (without `--tiers`) |
| **`ikp/REPRODUCTION.md`** | EN | Paper figure reproduction guide |
| **`ikp/data/README.md`** | EN | Data directory schema |
| **`ikp/scripts/README.md`** | EN | Full pipeline script index |
| **`ikp/website/README.md`** | EN | Website documentation |

## What's different from upstream

| | Upstream `ikp/` | This repo `ikp_study/` |
|---|---|---|
| `scripts/ikp_estimate.py` | Standard estimator | + `--tiers` filter; data path resolves into `ikp/` submodule |
| Documentation | English only | + Chinese translations of all docs |
| Project analysis | — | `PROJECT_ANALYSIS.md/.zh.md` (bilingual deep-dive) |

## Where to start

**"I want to estimate a model's parameter count"**
→ `TOOLKIT.md` → Quick start above

**"I want to test local/quantized models on hard probes only"**
→ `TOOLKIT.md` → "Testing local / quantized models on hard tiers (T4–T7)"

**"I want to understand how IKP works"**
→ `PROJECT_ANALYSIS.md` (EN) or `PROJECT_ANALYSIS.zh.md` (ZH)

**"I want to reproduce the paper figures"**
→ `ikp/REPRODUCTION.md` (EN) or `REPRODUCTION.zh.md` (ZH)

**"I want to explore the benchmark interactively"**
→ `ikp/README.md` → "Interactive CLI" section

**"I want to extend or re-calibrate IKP"**
→ `PROJECT_ANALYSIS.md` → "Extension Opportunities"
→ `ikp/scripts/README.md` → Dataset pipeline

---

<a name="chinese"></a>

---

# ikp_study（中文）

基于 [IKP（不可压缩知识探针）](https://github.com/19PINE-AI/ikp) 的研究仓库。IKP 是一个通过事实知识容量估算黑盒 LLM 参数量的基准测试。

上游项目位于 `ikp/` 子模块（只读）。本仓库新增：中文文档、双语项目分析，以及支持 `--tiers` 层级过滤的扩展估算脚本（适合本地/量化模型测试）。

## 快速开始

```bash
git clone --recurse-submodules https://github.com/host452b/ikp_study.git
cd ikp_study
pip install -r ikp/requirements.txt
export OPENROUTER_API_KEY=sk-or-...

# 完整基准（1,400 道题）
python scripts/ikp_estimate.py --model openai/gpt-4.1

# 本地/量化模型——只测困难层级
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model my-model --tiers T4,T5,T6,T7
```

## 文档导航

### 本仓库（`ikp_study/`）

| 文档 | 语言 | 说明 |
|---|---|---|
| **`README.md`** | 中/英 | 本文件——入口与文档导航 |
| **`README.zh.md`** | 中文 | ikp_study 中文概述 |
| **`TOOLKIT.md`** | 英文 | `scripts/ikp_estimate.py` CLI 参考，含 `--tiers` 说明及本地模型测试指南 |
| **`TOOLKIT.zh.md`** | 中文 | 同上（中文版） |
| **`PROJECT_ANALYSIS.md`** | 英文 | 深度解析：项目作用、方法论、工作流程、核心发现、扩展方向 |
| **`PROJECT_ANALYSIS.zh.md`** | 中文 | 同上（中文版） |
| **`REPRODUCTION.zh.md`** | 中文 | 论文图表复现指南（中文版） |
| **`data/README.zh.md`** | 中文 | 数据目录说明（中文版） |
| **`scripts/README.zh.md`** | 中文 | 脚本目录索引（中文版） |
| **`website/README.zh.md`** | 中文 | 网站构建与部署说明（中文版） |

### 上游子模块（`ikp/`）

| 文档 | 语言 | 说明 |
|---|---|---|
| **`ikp/README.md`** | 英文 | 上游项目概述与快速开始 |
| **`ikp/TOOLKIT.md`** | 英文 | 上游 CLI 参考（不含 `--tiers`） |
| **`ikp/REPRODUCTION.md`** | 英文 | 论文图表复现指南 |
| **`ikp/data/README.md`** | 英文 | 数据目录说明 |
| **`ikp/scripts/README.md`** | 英文 | 完整脚本流水线索引 |
| **`ikp/website/README.md`** | 英文 | 网站文档 |

## 与上游的区别

| | 上游 `ikp/` | 本仓库 `ikp_study/` |
|---|---|---|
| `scripts/ikp_estimate.py` | 标准估算器 | 新增 `--tiers` 过滤；数据路径自动指向 `ikp/` 子模块 |
| 文档 | 仅英文 | 新增所有文档的中文翻译 |
| 项目分析 | — | `PROJECT_ANALYSIS.md/.zh.md`（双语深度解析） |

## 按需快速导航

**「我想估算某个模型的参数量」**
→ `TOOLKIT.zh.md` → 快速开始

**「我想测试本地/量化模型的困难层级」**
→ `TOOLKIT.zh.md` → "本地量化模型 T4–T7 测试"

**「我想理解 IKP 的工作原理」**
→ `PROJECT_ANALYSIS.zh.md`

**「我想复现论文图表」**
→ `REPRODUCTION.zh.md`（中文）或 `ikp/REPRODUCTION.md`（英文）

**「我想交互式探索基准测试」**
→ `ikp/README.md` → "Interactive CLI" 章节

**「我想扩展或重新校准 IKP」**
→ `PROJECT_ANALYSIS.zh.md` → "扩展方向"
→ `ikp/scripts/README.md` → 数据集流水线
