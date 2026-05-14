# Benchmark Results: gpt-5.4 (effort=xhigh, Codex CLI)

**Date:** 2026-05-14
**Notes:** OpenAI ChatGPT-5.4 (the prior generation behind gpt-5.5) at `model_reasoning_effort="xhigh"`, accessed via the local `codex` CLI in headless mode. Run in parallel with the gpt-5.5 xhigh run on the same ChatGPT account for direct generational comparison.
**Environment:** macOS 25.2.0, `codex-cli` 0.125.0, NVIDIA corporate HTTP/HTTPS proxy
**Judge:** gpt-5.4 at `low` effort (self-judge bias acknowledged below)
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)
**Run shape:** 4 workers, concurrent with gpt-5.5 xhigh

---

## How to Run

```bash
HTTP_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
HTTPS_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
python scripts/ikp_estimate_codex_cli.py \
    --model gpt-5.4 --effort xhigh \
    --judge-model gpt-5.4 --judge-effort low \
    --workers 4 \
    --output results/gpt-5.4-codex-xhigh.json \
    --progress-file results/gpt-5.4-codex-xhigh.progress.jsonl
```

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | **71.2%** |
| Raw accuracy | 80.4% |
| **Estimated parameters** | **8.6T** |
| Effective tier | T6 (long-tail knowledge) |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 100% | 200 | 0 | 0 | 200 |
| T2 | 96% | 196 | 4 | 0 | 200 |
| T3 | 88% | 188 | 12 | 0 | 200 |
| T4 | 82% | 182 | 18 | 0 | 200 |
| T5 | 74% | 174 | 26 | 0 | 200 |
| T6 | 58% | 153 | 36 | 11 | 200 |
| T7 | 0% | 33 | 72 | 95 | 200 |

Effective tier: T6 — penalized accuracy 71.2% → estimated 8.6T parameters on the open-weight calibration curve (extrapolation; see caveat in `gpt-5.5-codex-xhigh.md`).

---

## Observations

### 5.4 vs 5.5 generational delta at matched effort
Direct comparison at xhigh (same script, same judge style, same concurrency):

| | T1 | T2 | T3 | T4 | T5 | T6 | T7 (correct) | Pen | Raw |
|---|---|---|---|---|---|---|---|---|---|
| **gpt-5.4 xhigh** | 100% | 96% | 88% | 82% | 74% | 58% | 33/200 | 71.2 | 80.4 |
| **gpt-5.5 xhigh** | 97% | 96% | 90% | 86% | 84% | 64% | 10/200 | 73.8 | 80.1 |

5.5 is consistently better at T3–T6 (the tiers where knowledge depth matters). Interestingly:
- **Raw accuracy is a tie** (80.4 vs 80.1) — both get roughly the same number of probes right overall.
- **Penalized accuracy gap is +2.6pp for 5.5** — driven entirely by refusal calibration. 5.5 refuses more on T7 (176 vs 95), so it eats far fewer wrong-answer penalties (T7 wrongs: 14 for 5.5 vs 72 for 5.4).

### 5.4 is the more confident hallucinator
At T7 (extreme long-tail), 5.4 is happy to commit:

| | correct | wrong | refusal |
|---|---|---|---|
| gpt-5.5 xhigh | 10 | 14 | 176 |
| **gpt-5.4 xhigh** | **33** | **72** | **95** |

5.4 gets more raw correct at T7 (33 vs 10) but at the cost of 5× the wrongs. This is the same pattern as gpt-5.5 at `low` effort — newer/more-thinking models learn to refuse rather than guess.

### Compared to the 4-model leaderboard
gpt-5.4 xhigh sits firmly above the prior best non-OpenAI runs:

| Model | Pen | T5 | T6 |
|---|---|---|---|
| gpt-5.5 xhigh | 73.8 | 84% | 64% |
| **gpt-5.4 xhigh** | **71.2** | **74%** | **58%** |
| gpt-5.5 low | 67.1 | 72% | 50% |
| Sonnet 4.6 max | 57.1 | 39% | 0% |
| Opus 4.7 | 52.6 | 25% | 6% |

5.4 at xhigh beats 5.5 at low — the reasoning-effort lever buys more than a generation gap in this regime.

---

## Self-Judge Bias

Subject and judge both gpt-5.4 (judge at low effort). Same caveat as the gpt-5.5 run — CORRECT verdicts skew up modestly versus an independent judge.

---

## See Also

- [`gpt-5.5-codex-xhigh.md`](gpt-5.5-codex-xhigh.md) — sibling run, current model generation
- [`gpt-5.5-codex.md`](gpt-5.5-codex.md) — gpt-5.5 at low effort, for the effort comparison
- [`../TOOLKIT_AGENT.md`](../TOOLKIT_AGENT.md) — script reference for the Agent path
