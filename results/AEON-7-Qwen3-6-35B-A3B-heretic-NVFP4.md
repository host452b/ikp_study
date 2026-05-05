# Benchmark Results: AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4

**Date:** 2026-04-30  
**Notes:** Community NVFP4 fine-tune of Qwen3.6-35B-A3B  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ with an independent judge.

---

## How to Run

```
# 1. Start vLLM server
vllm serve AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4 \
    --port 8000 --tensor-parallel-size 1 \
    --max-model-len 4096 --gpu-memory-utilization 0.9

# 2. Run benchmark
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4 \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4 \
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
| Penalized accuracy | 36.9% |
| Raw accuracy | 50.7% |
| **Estimated parameters** | **40B** |
| Effective tier | T4 |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 99% | 199 | 1 | 0 | 200 |
| T2 | 97% | 197 | 3 | 0 | 200 |
| T3 | 55% | 154 | 44 | 2 | 200 |
| T4 | 7% | 100 | 86 | 14 | 200 |
| T5 | 0% | 26 | 131 | 43 | 200 |
| T6 | 0% | 17 | 114 | 69 | 200 |
| T7 | 0% | 17 | 114 | 69 | 200 |

Effective tier: T4 — estimated 40B.

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
