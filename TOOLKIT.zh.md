# IKP 估算工具包 —— HTTP API 路径（vLLM / OpenRouter）

> **两条路径，两份工具说明。** 本文档介绍 **HTTP API 路径**——
> `scripts/ikp_estimate.py`，向任意 OpenAI 兼容端点（vLLM、llama.cpp、Ollama、OpenRouter…）发请求。
>
> 如果要在没有 Anthropic API Key 的情况下评估 Claude Code 模型，请走
> **Agent 路径**（[`TOOLKIT_AGENT.zh.md`](TOOLKIT_AGENT.zh.md)）——
> 它通过 shell 调用 `claude -p`，不走 HTTP。

本文档介绍**本仓库**（`ikp_study/`）中的 `scripts/ikp_estimate.py`，
该脚本在上游 [`ikp/scripts/ikp_estimate.py`](ikp/TOOLKIT.md) 基础上新增：

- `--tiers` — 只运行指定层级的探针
- 数据路径自动指向 `ikp/` 子模块

上游原版 CLI 参考见 [`ikp/TOOLKIT.md`](ikp/TOOLKIT.md)。

## 一键运行

```bash
export OPENROUTER_API_KEY=sk-or-...
python scripts/ikp_estimate.py --model openai/gpt-4.1
```

## CLI 参考

### 评测设置（新增 --tiers）

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--sample, -n N` | 全部 1400 | 分层随机采样：每层 `N/7` 个探针。 |
| `--tiers TIERS` | 全部 7 层 | 逗号分隔的层级，如 `T4,T5,T6,T7`。准确率仅在所测层级上取均值。 |
| `--workers, -w N` | 16 | 并行请求数。 |
| `--sequential, -s` | 关闭 | 强制串行（`workers=1`）。 |
| `--output, -o FILE` | — | 导出完整逐探针结果为 JSON。 |

### 模型设置

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--model, -m MODEL` | — | 目标模型 ID，如 `openai/gpt-4.1`。 |
| `--api-base URL` | `https://openrouter.ai/api/v1` | 任意 OpenAI 兼容端点。 |
| `--api-key KEY` | `$OPENROUTER_API_KEY` | `--api-base` 的 Bearer 令牌。 |
| `--thinking` | 关闭 | 向模型传递 `reasoning: {"effort":"medium"}`。 |

### 检查 / 信息

| 参数 | 用途 |
|---|---|
| `--inspect` | 评分后打印每道题的模型回答、标准答案和评测结果。 |
| `--inspect-probes` | 打印探针集后退出（不调用 API）。 |
| `--show-calibration` | 打印校准公式、参考点和 R²。 |

## 本地量化模型 T4–T7 测试

### 支持的本地推理服务

| 服务 | 默认 API 地址 | 启动示例 |
|---|---|---|
| **vLLM** | `http://localhost:8000/v1` | `vllm serve ./model --port 8000` |
| **llama.cpp server** | `http://localhost:8080/v1` | `./llama-server -m model.gguf --port 8080` |
| **Ollama** | `http://localhost:11434/v1` | `ollama serve` |
| **LM Studio** | `http://localhost:1234/v1` | 从界面启动 |

`OPENROUTER_API_KEY` 始终必需（供 Gemini 裁判使用）。T4–T7 完整测试裁判费用约 **$0.05–0.20**。

### 单个模型，只跑 T4–T7

```bash
export OPENROUTER_API_KEY=sk-or-...

python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model-name \
    --tiers    T4,T5,T6,T7
```

加 `--sample 280` 每层只跑 70 道，速度快约 3 倍：

```bash
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model-name \
    --tiers    T4,T5,T6,T7 \
    --sample   280 \
    --output   results/my-model.json
```

### 批量对比多个量化版本

```bash
#!/bin/bash
export OPENROUTER_API_KEY=sk-or-...

MODELS=(
  "Qwen3-30B-A3B-Q4"
  "Qwen3-30B-A3B-Q8"
  "Llama-3-70B-Q4_K_M"
  "Llama-3-70B-Q8_0"
)

mkdir -p results/local_quant

for MODEL in "${MODELS[@]}"; do
    echo "=== $MODEL ==="
    python scripts/ikp_estimate.py \
        --api-base http://localhost:8000/v1 \
        --api-key  EMPTY \
        --model    "$MODEL" \
        --tiers    T4,T5,T6,T7 \
        --output   "results/local_quant/${MODEL}.json"
done
```

> 模型名称须与推理服务注册的标识符一致——vLLM 通过 `--served-model-name` 指定；Ollama 使用模型 tag。

### 正式运行前快速预览

```bash
# 查看 T4–T7 题目样例
python scripts/ikp_estimate.py --inspect-probes | grep -A4 "── T4 ──" | head -20

# 每层 8 题，查看逐题输出
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model \
    --tiers    T4,T5,T6,T7 \
    --sample   56 \
    --inspect
```

### 解读部分层级结果

使用 `--tiers` 时，参数量估算基于**所测层级均值**，而非完整 7 层均值。该数值应用于自有模型变体的**相对排名**，不代表真实规模。
