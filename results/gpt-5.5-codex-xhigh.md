# Benchmark Results: gpt-5.5 (effort=xhigh, Codex CLI)

**Date:** 2026-05-14
**Notes:** OpenAI ChatGPT-5.5, accessed via the local `codex` CLI in headless mode (`codex exec`) at `model_reasoning_effort="xhigh"`. This is the **highest working effort** — `max` returns empty strings, so xhigh is the practical ceiling.
**Environment:** macOS 25.2.0, `codex-cli` 0.125.0, NVIDIA corporate HTTP/HTTPS proxy
**Judge:** gpt-5.5 at `low` effort (same `codex exec` path — self-judge bias acknowledged below)
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)
**Run shape:** 4 workers (concurrent with a second gpt-5.4 xhigh run on the same ChatGPT account, so the Codex variant defaulted to a lower workers count than the Claude variant to share rate-limit headroom)

---

## How to Run

```bash
HTTP_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
HTTPS_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
python scripts/ikp_estimate_codex_cli.py \
    --model gpt-5.5 --effort xhigh \
    --judge-model gpt-5.5 --judge-effort low \
    --workers 4 \
    --output results/gpt-5.5-codex-xhigh.json \
    --progress-file results/gpt-5.5-codex-xhigh.progress.jsonl
```

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | **73.8%** |
| Raw accuracy | 80.1% |
| **Estimated parameters** | **12.9T** |
| Effective tier | T6 (long-tail knowledge — only the largest models) |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 97% | 197 | 3 | 0 | 200 |
| T2 | 96% | 196 | 4 | 0 | 200 |
| T3 | 90% | 190 | 10 | 0 | 200 |
| T4 | 86% | 186 | 14 | 0 | 200 |
| T5 | 84% | 184 | 16 | 0 | 200 |
| T6 | 64% | 158 | 31 | 11 | 200 |
| T7 | 0% | 10 | 14 | 176 | 200 |

Effective tier: T6 — penalized accuracy 73.8% → estimated 12.9T parameters on the 89-model open-weight calibration curve (well beyond the curve's anchor range; see Calibration caveat).

---

## Observations

### Highest IKP score in this repo
73.8% penalized is the highest mark across every model run so far. The next-closest models in `benchmark.csv`:

| Model | Pen | T5 | T6 |
|---|---|---|---|
| **gpt-5.5 xhigh** | **73.8** | **84%** | **64%** |
| gpt-5.4 xhigh | 71.2 | 74% | 58% |
| gpt-5.5 low | 67.1 | 72% | 50% |
| Sonnet 4.6 max | 57.1 | 39% | 0% |
| Opus 4.7 | 52.6 | 25% | 6% |

The T5 and T6 cliffs that defeat other models barely register: T5 stays at 84%, T6 still holds 64%.

### xhigh vs low — what does +6.7pp buy?
Compared to the earlier `low`-effort gpt-5.5 run, xhigh adds:

| | T1 | T2 | T3 | T4 | T5 | T6 | T7 (correct) |
|---|---|---|---|---|---|---|---|
| low effort | 98% | 96% | 86% | 68% | 72% | 50% | 80/200 |
| xhigh | 97% | 96% | 90% | 86% | 84% | 64% | 10/200 |

Gains concentrate at T4–T6 (the tiers where the model *can* know but has to retrieve carefully). T7 actually got **worse** in raw correct count (80 → 10), but **better** in penalized score — xhigh learns to refuse instead of guessing. The 176 refusals at T7 (vs 38 at low) drive penalized score up because wrongs cost −1.0 while refusals cost 0.

### xhigh changes hallucination calibration
At low effort, gpt-5.5 hallucinated heavily on T7 (82 wrong, 38 refusal). At xhigh:

| | wrong at T7 | refusal at T7 |
|---|---|---|
| low | 82 | 38 |
| xhigh | 14 | 176 |

More thinking budget → the model recognises its own knowledge boundary. Closer to Opus's pattern, but Opus is much more aggressive (T7: 23 wrong / 170 refusal at default).

### Calibration caveat
The 12.9T estimate is way off the calibration curve's anchor range (89 open-weight models, 135M–1.6T). The mapping `log10(params_B) = 6.79 × penalized_acc − 0.899` was fit on accuracies up to ~63%; extrapolating to 73.8% yields a multi-trillion number with enormous confidence intervals. Read as *"open-weight scaling law projection"*, not as ground truth — gpt-5.5's actual parameter count is undisclosed and almost certainly nowhere near 13T.

---

## Self-Judge Bias

Both subject and judge use gpt-5.5 (judge at low effort). CORRECT verdicts skew up because the judge recognises the subject's preferred phrasing. The Claude path uses an independent judge (Haiku 4.5); cross-comparing gpt-5.5 numbers against Sonnet 4.6 max or Opus 4.7 carries a small systematic offset in gpt-5.5's favour.

---

## See Also

- [`gpt-5.4-codex-xhigh.md`](gpt-5.4-codex-xhigh.md) — sibling run, prior model generation
- [`gpt-5.5-codex.md`](gpt-5.5-codex.md) — same model at `low` effort
- [`claude-sonnet-4-6-max.md`](claude-sonnet-4-6-max.md) — Anthropic counterpart at max effort
- [`../TOOLKIT_AGENT.md`](../TOOLKIT_AGENT.md) — script reference for the Agent path
