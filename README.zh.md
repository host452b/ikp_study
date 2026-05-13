# 不可压缩知识探针（IKP）

> 上游项目：[19PINE-AI/ikp](https://github.com/19PINE-AI/ikp)（位于 `ikp/` 子模块）
>
> 本仓库（`ikp_study`）在上游基础上新增：中文文档、双语项目分析、以及支持 `--tiers` 过滤的修改版估算脚本。

IKP 是一个包含 1,400 道题的事实性基准测试——200 题 × 7 个难度层级（T1：通识知识 … T7：极长尾知识）。在 89 个参数量从 1.35 亿到 1.6 万亿的开源模型上，IKP 准确率与参数量呈**对数线性关系**（R² = 0.917），因此只需一次黑盒 API 调用，即可估算任意已部署模型（包括闭源前沿模型）的有效知识容量。

## 快速开始

```bash
git clone --recurse-submodules https://github.com/host452b/ikp_study.git
cd ikp_study
pip install -r ikp/requirements.txt

# ── 路径 A：HTTP API（vLLM / OpenRouter）──
export OPENROUTER_API_KEY=sk-or-...

# 完整估算（使用本仓库修改版脚本，支持 --tiers）
python scripts/ikp_estimate.py --model openai/gpt-4.1

# 只测困难层级（T4–T7），适合本地量化模型
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-local-model \
    --tiers    T4,T5,T6,T7

# ── 路径 B：Agent（通过 claude -p，无需 Anthropic API Key）──
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 --judge-model claude-haiku-4-5 -w 8
```

也可直接使用上游脚本（不含 `--tiers`）：

```bash
python ikp/scripts/ikp_estimate.py --model openai/gpt-4.1
```

## 本仓库新增内容

| 文件 | 说明 |
|---|---|
| `scripts/ikp_estimate.py` | 修改版估算脚本（HTTP API 路径），新增 `--tiers` 层级过滤 |
| `scripts/ikp_estimate_claude_cli.py` | Agent 路径估算脚本，通过 `claude -p` 子进程测评（无需 Anthropic API Key） |
| `README.zh.md` | 本文件（中文说明） |
| `TOOLKIT.md` | HTTP API 路径 CLI 参考（英文） |
| `TOOLKIT.zh.md` | HTTP API 路径 CLI 参考（中文） |
| `TOOLKIT_AGENT.md` | Agent 路径 CLI 参考（英文） |
| `TOOLKIT_AGENT.zh.md` | Agent 路径 CLI 参考（中文） |
| `REPRODUCTION.zh.md` | 论文复现指南中文版 |
| `PROJECT_ANALYSIS.md` | 项目深度解析（英文） |
| `PROJECT_ANALYSIS.zh.md` | 项目深度解析（中文） |
| `data/README.zh.md` | 数据目录说明中文版 |
| `scripts/README.zh.md` | 脚本目录说明中文版 |
| `website/README.zh.md` | 网站部署说明中文版 |

## 本地量化模型测试（T4–T7）

```bash
# 单个模型
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model my-model --tiers T4,T5,T6,T7

# 批量对比多个量化版本
for MODEL in Q4_K_M Q6_K Q8_0; do
    python scripts/ikp_estimate.py \
        --api-base http://localhost:8000/v1 --api-key EMPTY \
        --model "Llama-3-70B-${MODEL}" \
        --tiers T4,T5,T6,T7 \
        --output "results/${MODEL}.json"
done
```

详细用法见 [`TOOLKIT.zh.md`](TOOLKIT.zh.md)。

## 仓库结构

```
ikp_study/
├── ikp/                              ← 子模块 → 19PINE-AI/ikp（上游原版）
├── scripts/
│   ├── ikp_estimate.py               ← HTTP API 路径（vLLM/OpenRouter，新增 --tiers）
│   └── ikp_estimate_claude_cli.py    ← Agent 路径（通过 claude -p）
├── README.zh.md                      ← 本文件
├── TOOLKIT.md                        ← HTTP API CLI 参考（英文）
├── TOOLKIT.zh.md                     ← HTTP API CLI 参考（中文）
├── TOOLKIT_AGENT.md                  ← Agent CLI 参考（英文）
├── TOOLKIT_AGENT.zh.md               ← Agent CLI 参考（中文）
├── REPRODUCTION.zh.md      ← 论文复现指南（中文）
├── PROJECT_ANALYSIS.md     ← 项目深度解析（英文）
├── PROJECT_ANALYSIS.zh.md  ← 项目深度解析（中文）
├── data/README.zh.md
├── scripts/README.zh.md
└── website/README.zh.md
```

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
