# IKP 估算工具包

`scripts/ikp_estimate.py` 是一个自包含的 CLI，可将模型在 1,400 个探针的 IKP 基准上评分，并通过论文中校准的对数线性曲线将结果映射为有效参数量估算值。

## 安装

```bash
pip install -r requirements.txt
```

Python ≥ 3.10，Linux/macOS。无需 GPU——本工具仅调用 API 端点。

## 一键运行

```bash
export OPENROUTER_API_KEY=sk-or-...
python scripts/ikp_estimate.py --model openai/gpt-4.1
```

该工具将：(1) 发送健全性检查探针，(2) 用 16 个并行 worker 发送 1,400 个探针，(3) 用 Gemini 3 Flash Preview 对每个答案评分，(4) 打印每层级分项结果和估算的参数量。典型每次运行成本：**$0.10–$3**。

## CLI 参考

```
python scripts/ikp_estimate.py [选项]
```

### 模型设置

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--model, -m MODEL` | — | 目标模型 ID，如 `openai/gpt-4.1`、`anthropic/claude-opus-4.7`。 |
| `--api-base URL` | `https://openrouter.ai/api/v1` | 任意 OpenAI 兼容端点（OpenRouter、OpenAI、vLLM、llama-server 等）。 |
| `--api-key KEY` | `$OPENROUTER_API_KEY` | `--api-base` 的 Bearer 令牌。 |
| `--thinking` | 关闭 | 向目标模型传递 `reasoning: {"effort":"medium"}`，适用于 `-think` 变体。 |

### 评测设置

| 参数 | 默认值 | 用途 |
|---|---|---|
| `--sample, -n N` | 全部 1400 | 分层随机采样：每层 `N/7` 个探针。用 200–400 进行快速初步测试。 |
| `--tiers TIERS` | 全部 7 层 | 逗号分隔的层级列表，如 `T4,T5,T6,T7`。准确率仅在所测层级上取均值。适合只测本地/量化模型的困难探针。 |
| `--workers, -w N` | 16 | 并行请求数。如提供商有速率限制，可适当降低。 |
| `--sequential, -s` | 关闭 | 强制 `workers=1`（串行模式）。 |
| `--output, -o FILE` | — | 将完整的逐探针结果及校准元数据导出为 JSON。 |

### 检查 / 信息

| 参数 | 用途 |
|---|---|
| `--inspect` | 评分完成后，按层级打印每个探针的模型回答、标准答案和评测结果。 |
| `--inspect-probes` | 不调用 API；直接按层级打印探针集后退出。 |
| `--show-calibration` | 打印校准公式、参考点和 R²，然后退出。 |

## 环境变量

| 变量 | 是否必需 | 用途 |
|---|---|---|
| `OPENROUTER_API_KEY` | 始终需要（供裁判使用） | `google/gemini-3-flash-preview` 裁判调用 |

## 估算计算方式

1. 每个探针以单轮用户消息发送，系统提示为直接简洁回答或说"I don't know"。
2. 裁判返回 `CORRECT | WRONG | REFUSAL`。错误答案按 **−1.0** 惩罚；拒绝计为 0。
3. 对每个层级：`tier_score = max(0, (correct − wrong) / total)`。
4. `accuracy = mean(tier_score)`，对已测层级取均值。
5. `log10(params_B) = 6.790 · accuracy − 0.899`。

## 已知局限

- **快照性质。** 校准反映 2024 年末至 2026 年初的网络事实分布，需定期重校准。
- **激进安全调优。** 拒绝率高的模型会被低估。
- **探针样本过小。** `--sample` < 100 时预测区间明显变宽。
- **仅限英文知识。** 专门针对非英文语言优化的模型会被低估。

## 快速示例

```bash
# 快速初步测试（约 1 分钟，约 $0.05）
python scripts/ikp_estimate.py --model openai/gpt-4.1 --sample 140

# 本地托管的 vLLM
OPENROUTER_API_KEY=... python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model meta-llama/Meta-Llama-3-70B-Instruct

# 思考模式对比
python scripts/ikp_estimate.py -m anthropic/claude-opus-4.7
python scripts/ikp_estimate.py -m anthropic/claude-opus-4.7 --thinking

# 导出结果供事后分析
python scripts/ikp_estimate.py -m openai/gpt-5 -o runs/gpt-5.json

# 先查看校准曲线，不消耗任何 token
python scripts/ikp_estimate.py --show-calibration
python scripts/ikp_estimate.py --inspect-probes | head -40
```

## 本地量化模型的 T4–T7 测试

本地量化模型（GGUF、AWQ、GPTQ 等）可以只测更难的层级，跳过 7B 以上模型几乎全对的 T1–T3 探针。

### 支持的本地推理服务

| 服务 | 默认 API 地址 | 启动示例 |
|---|---|---|
| **vLLM** | `http://localhost:8000/v1` | `vllm serve ./model --port 8000` |
| **llama.cpp server** | `http://localhost:8080/v1` | `./llama-server -m model.gguf --port 8080` |
| **Ollama** | `http://localhost:11434/v1` | `ollama serve` |
| **LM Studio** | `http://localhost:1234/v1` | 从界面启动 |

裁判始终在 OpenRouter 上运行，因此即使目标模型完全本地化，也必须设置 `OPENROUTER_API_KEY`。T4–T7 完整测试的裁判费用约 **$0.05–0.20**。

### 单个模型，只跑 T4–T7

```bash
export OPENROUTER_API_KEY=sk-or-...

python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model-name \
    --tiers    T4,T5,T6,T7
```

加 `--sample 280` 可每层只跑 70 道，速度快约 3 倍：

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
# test_local_models.sh
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

> 模型名称须与推理服务中注册的标识符一致——vLLM 通过 `--served-model-name` 指定；Ollama 使用模型 tag。

### 正式运行前快速预览

```bash
# 查看 T4–T7 题目样例
python scripts/ikp_estimate.py --inspect-probes | grep -A4 "── T4 ──" | head -20

# 跑 56 道题并查看每题输出（每层 8 题）
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model \
    --tiers    T4,T5,T6,T7 \
    --sample   56 \
    --inspect
```

### 解读部分层级结果

使用 `--tiers` 时，显示的参数量估算是校准曲线应用于**所测层级均值**的结果，而非完整 7 层均值。该绝对数值与论文报告的规模不可直接比较——应将其用于自有模型变体间的**相对排名**。

## 批量评测（为名单贡献数据）

```bash
python scripts/run_all_models.py --skip-existing            # 完整名单
python scripts/run_all_models.py --vendor openai            # 单一供应商
python scripts/run_all_models.py --type open --max-models 10
```

每次运行都会向 `data/results/evaluation_summary.json` 追加一行。详见 `REPRODUCTION.zh.md`。
