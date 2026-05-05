# Benchmark Results: moonshotai/Kimi-VL-A3B-Instruct

**Date:** 2026-04-30  
**Notes:** Kimi VL, ~3B active (MoE), --trust-remote-code  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ with an independent judge.

---

## How to Run

```
# 1. Start vLLM server
vllm serve moonshotai/Kimi-VL-A3B-Instruct \
    --port 8000 --tensor-parallel-size 1 \
    --max-model-len 4096 --gpu-memory-utilization 0.9
    --trust-remote-code \

# 2. Run benchmark
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model moonshotai/Kimi-VL-A3B-Instruct \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model moonshotai/Kimi-VL-A3B-Instruct \
    --workers 8
```

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 24.4% |
| Raw accuracy | 37.0% |
| **Estimated parameters** | **6B** |
| Effective tier | T2 |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 92% | 192 | 8 | 0 | 200 |
| T2 | 79% | 179 | 21 | 0 | 200 |
| T3 | 0% | 91 | 109 | 0 | 200 |
| T4 | 0% | 25 | 175 | 0 | 200 |
| T5 | 0% | 13 | 187 | 0 | 200 |
| T6 | 0% | 10 | 190 | 0 | 200 |
| T7 | 0% | 8 | 192 | 0 | 200 |

Effective tier: T2 — estimated 6B.

---

## Issues and Fixes

### Self-judge bias

Using the same model as both subject and judge means correct answers are more
likely to be judged CORRECT (the model recognises its own phrasing). For
production use, an independent judge model is recommended.
