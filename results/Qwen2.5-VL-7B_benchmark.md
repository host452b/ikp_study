# Benchmark Results: Qwen2.5-VL-7B (FP8 vs BF16)

**Date:** 2026-04-30  
**Environment:** vLLM 0.20.0, 1× NVIDIA GPU (183 GB VRAM)  
**Judge:** same local model (self-judge) via `--judge-api-base http://localhost:8000/v1`  
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

> Note: self-judging introduces a circular bias — the model grades its own answers.
> Results are directionally valid but would differ slightly with an independent judge.

---

## Run 1 — nvidia/Qwen2.5-VL-7B-Instruct-FP8 (full, no thinking)

```
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model nvidia/Qwen2.5-VL-7B-Instruct-FP8 \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model nvidia/Qwen2.5-VL-7B-Instruct-FP8 \
    --workers 8
```

| Metric | Value |
|---|---|
| Penalized accuracy | 26.1% |
| Raw accuracy | 39.3% |
| **Estimated parameters** | **7B** |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 96% | 196 | 4 | 0 | 200 |
| T2 | 86% | 186 | 13 | 1 | 200 |
| T3 | 0% | 81 | 112 | 7 | 200 |
| T4 | 0% | 38 | 138 | 24 | 200 |
| T5 | 0% | 20 | 123 | 57 | 200 |
| T6 | 0% | 14 | 126 | 60 | 200 |
| T7 | 0% | 15 | 95 | 90 | 200 |

Effective tier: T2 — estimate matches actual parameter count.

---

## Run 2 — nvidia/Qwen2.5-VL-7B-Instruct-FP8 (full, --thinking)

```
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model nvidia/Qwen2.5-VL-7B-Instruct-FP8 \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model nvidia/Qwen2.5-VL-7B-Instruct-FP8 \
    --thinking --workers 4
```

| Metric | Value |
|---|---|
| Penalized accuracy | 26.1% |
| Raw accuracy | 39.3% |
| **Estimated parameters** | **8B** |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 98% | 198 | 2 | 0 | 200 |
| T2 | 85% | 185 | 15 | 0 | 200 |
| T3 | 0% | 85 | 108 | 7 | 200 |
| T4 | 0% | 35 | 137 | 28 | 200 |
| T5 | 0% | 20 | 123 | 57 | 200 |
| T6 | 0% | 10 | 124 | 66 | 200 |
| T7 | 0% | 17 | 98 | 85 | 200 |

Thinking mode: T1 +2 correct, T3 +4 correct / −4 wrong. Marginal improvement; T3 remains negative after penalty. Estimate within IKP's ±1.6× LOO error band.

---

## Run 3 — Qwen/Qwen2.5-VL-7B-Instruct (BF16, full, no thinking)

```
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 --api-key EMPTY \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --judge-api-base http://localhost:8000/v1 \
    --judge-model Qwen/Qwen2.5-VL-7B-Instruct \
    --workers 8
```

| Metric | Value |
|---|---|
| Penalized accuracy | 26.1% |
| Raw accuracy | 38.1% |
| **Estimated parameters** | **7B** |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 97% | 197 | 3 | 0 | 200 |
| T2 | 86% | 185 | 14 | 1 | 200 |
| T3 | 0% | 87 | 104 | 9 | 200 |
| T4 | 0% | 35 | 143 | 22 | 200 |
| T5 | 0% | 15 | 119 | 66 | 200 |
| T6 | 0% | 4 | 128 | 68 | 200 |
| T7 | 0% | 11 | 95 | 94 | 200 |

Effective tier: T2 — identical estimate to FP8 version.

---

## Summary

| Model | Quantization | Thinking | Penalized Acc | Estimated |
|---|---|---|---|---|
| nvidia/Qwen2.5-VL-7B-Instruct-FP8 | FP8 | No | 26.1% | **7B** |
| nvidia/Qwen2.5-VL-7B-Instruct-FP8 | FP8 | Yes | 26.1% | **8B** |
| Qwen/Qwen2.5-VL-7B-Instruct | BF16 | No | 26.1% | **7B** |

**FP8 quantization loss is negligible** — identical penalized accuracy (26.1%) and same 7B estimate.
Thinking mode gives a marginal +4 correct on T3 but not enough to flip the penalized score positive.

Knowledge boundary sits firmly at T2/T3, consistent with a 7B-class model.

---

## Observations on REFUSAL behavior

T6/T7 refusals (50–90 per tier) are expected and correct: the model says "I don't know" on
extreme long-tail probes (obscure researchers, minor infrastructure) that a 7B model has not
memorized. This is preferable to hallucinating confident wrong answers (which incur −1 penalty).
T3/T4 show lower refusal rates but higher wrong counts, indicating the model guesses more
confidently in its partial-knowledge zone.
