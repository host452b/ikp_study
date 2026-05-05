# Benchmark Results: Qwen/Qwen3-32B

**Date:** 2026-04-30  
**Notes:** Qwen3 dense 32B, BF16  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ with an independent judge.

---

## How to Run

```
# 1. Start vLLM server
vllm serve Qwen/Qwen3-32B \
    --port 8000 --tensor-parallel-size 1 \
    --max-model-len 4096 --gpu-memory-utilization 0.9

# 2. Run benchmark
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model Qwen/Qwen3-32B \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model Qwen/Qwen3-32B \
    --workers 8
```

> **Qwen3 note:** This script auto-disables internal thinking via
> `chat_template_kwargs={"enable_thinking": false}` for Qwen3 models.

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 30.7% |
| Raw accuracy | 31.9% |
| **Estimated parameters** | **15B** |
| Effective tier | T3 |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 97% | 197 | 3 | 0 | 200 |
| T2 | 97% | 197 | 3 | 0 | 200 |
| T3 | 21% | 53 | 11 | 136 | 200 |
| T4 | 0% | 0 | 0 | 200 | 200 |
| T5 | 0% | 0 | 0 | 200 | 200 |
| T6 | 0% | 0 | 0 | 200 | 200 |
| T7 | 0% | 0 | 0 | 200 | 200 |

Effective tier: T3 — estimated 15B.

---

## Issues and Fixes

### Self-judge bias

Using the same model as both subject and judge means correct answers are more
likely to be judged CORRECT (the model recognises its own phrasing). For
production use, an independent judge model is recommended.
