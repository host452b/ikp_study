# Benchmark Results: deepseek-ai/DeepSeek-V4-Flash

**Date:** 2026-04-30  
**Notes:** DeepSeek V4 Flash, --kv-cache-dtype fp8  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ with an independent judge.

---

## How to Run

```
# 1. Start vLLM server
vllm serve deepseek-ai/DeepSeek-V4-Flash \
    --port 8000 --tensor-parallel-size 1 \
    --max-model-len 4096 --gpu-memory-utilization 0.9
    --kv-cache-dtype fp8 \

# 2. Run benchmark
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model deepseek-ai/DeepSeek-V4-Flash \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model deepseek-ai/DeepSeek-V4-Flash \
    --workers 8
```

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 45.4% |
| Raw accuracy | 63.1% |
| **Estimated parameters** | **152B** |
| Effective tier | T5 |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 74% | 174 | 26 | 0 | 200 |
| T2 | 93% | 193 | 7 | 0 | 200 |
| T3 | 71% | 171 | 29 | 0 | 200 |
| T4 | 58% | 158 | 41 | 1 | 200 |
| T5 | 21% | 114 | 72 | 14 | 200 |
| T6 | 0% | 64 | 102 | 34 | 200 |
| T7 | 0% | 10 | 123 | 67 | 200 |

Effective tier: T5 — estimated 152B.

---

## Issues and Fixes

### Self-judge bias

Using the same model as both subject and judge means correct answers are more
likely to be judged CORRECT (the model recognises its own phrasing). For
production use, an independent judge model is recommended.
