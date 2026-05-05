# Benchmark Results: moonshotai/Kimi-VL-A3B-Instruct

**Date:** 2026-04-30  
**Notes:** Kimi VL, ~3B active (MoE)  
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
| Penalized accuracy | 0% |
| Raw accuracy | 0% |
| **Estimated parameters** | **SKIPPED** |
| Effective tier | N/A |

Effective tier: N/A — estimated SKIPPED.

---

## Issues and Fixes

### Self-judge bias

Using the same model as both subject and judge means correct answers are more
likely to be judged CORRECT (the model recognises its own phrasing). For
production use, an independent judge model is recommended.
