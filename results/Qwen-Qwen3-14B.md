# Benchmark Results: Qwen/Qwen3-14B

**Date:** 2026-04-30  
**Notes:** Qwen3 dense 14B, BF16  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ with an independent judge.

---

## How to Run

```
# 1. Start vLLM server
vllm serve Qwen/Qwen3-14B \
    --port 8000 --tensor-parallel-size 1 \
    --max-model-len 4096 --gpu-memory-utilization 0.9

# 2. Run benchmark
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model Qwen/Qwen3-14B \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model Qwen/Qwen3-14B \
    --workers 8
```

> **Qwen3 note:** This script auto-disables internal thinking via
> `chat_template_kwargs={"enable_thinking": false}` for Qwen3 models.

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 31.1% |
| Raw accuracy | 42.1% |
| **Estimated parameters** | **16B** |
| Effective tier | T3 |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 95% | 195 | 5 | 0 | 200 |
| T2 | 90% | 190 | 10 | 0 | 200 |
| T3 | 32% | 131 | 66 | 3 | 200 |
| T4 | 0% | 50 | 140 | 10 | 200 |
| T5 | 0% | 11 | 143 | 46 | 200 |
| T6 | 0% | 4 | 106 | 90 | 200 |
| T7 | 0% | 8 | 114 | 78 | 200 |

Effective tier: T3 — estimated 16B.

---

## Issues and Fixes

### Self-judge bias

Using the same model as both subject and judge means correct answers are more
likely to be judged CORRECT (the model recognises its own phrasing). For
production use, an independent judge model is recommended.
