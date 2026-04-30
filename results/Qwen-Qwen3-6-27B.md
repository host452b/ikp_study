# Benchmark Results: Qwen/Qwen3.6-27B

**Date:** 2026-04-30  
**Notes:** Dense 27B, BF16  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ with an independent judge.

---

## How to Run

```
# 1. Start vLLM server
vllm serve Qwen/Qwen3.6-27B \
    --port 8000 --tensor-parallel-size 1 \
    --max-model-len 4096 --gpu-memory-utilization 0.9

# 2. Run benchmark
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model Qwen/Qwen3.6-27B \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model Qwen/Qwen3.6-27B \
    --workers 8
```

> **Qwen3 note:** This script auto-disables internal thinking via
> `chat_template_kwargs={"enable_thinking": false}` for Qwen3 models.
> Without this, the model outputs multi-paragraph reasoning into `content`
> and the judge classifies everything as WRONG. See Issues section below.

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 36.1% |
| Raw accuracy | 48.4% |
| **Estimated parameters** | **36B** |
| Effective tier | T3 |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 98% | 198 | 2 | 0 | 200 |
| T2 | 96% | 196 | 4 | 0 | 200 |
| T3 | 59% | 156 | 38 | 6 | 200 |
| T4 | 0% | 77 | 100 | 23 | 200 |
| T5 | 0% | 30 | 115 | 55 | 200 |
| T6 | 0% | 8 | 77 | 115 | 200 |
| T7 | 0% | 12 | 99 | 89 | 200 |

Effective tier: T3 — estimated 36B.

---

## Issues and Fixes

### Qwen3 default thinking mode

**Problem:** Qwen3 models embed their chain-of-thought reasoning directly into
the `content` field of the API response by default. During an early run on
`Qwen/Qwen3.6-35B-A3B`, every probe returned 0 correct because the judge
received a multi-paragraph thinking trace and could not extract a verdict.

**Fix:** Added `is_qwen3_model()` in `scripts/ikp_estimate.py`. When the
model name contains `qwen3` (case-insensitive) and `--thinking` is not set,
both the query and judge payloads include:
```json
{"chat_template_kwargs": {"enable_thinking": false}}
```
This produces clean, one-line factual answers compatible with IKP scoring.

### Self-judge bias

Using the same model as both subject and judge means correct answers are more
likely to be judged CORRECT (the model recognises its own phrasing). For
production use, an independent judge model is recommended.
