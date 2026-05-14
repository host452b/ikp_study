# Benchmark Results: claude-sonnet-4-6 (effort=max, Claude Code)

**Date:** 2026-05-14
**Notes:** Anthropic Claude Sonnet 4.6, accessed via the local `claude` CLI in headless mode with `--effort max`. Same Agent path as the Opus 4.7 run, different model + reasoning effort.
**Environment:** macOS 25.2.0, `claude` CLI 2.1.140, NVIDIA corporate HTTP/HTTPS proxy
**Judge:** `claude-haiku-4-5` (default judge effort) — independent from the subject model, avoids self-judging bias
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)

---

## How to Run

```bash
HTTP_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
HTTPS_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
python scripts/ikp_estimate_claude_cli.py \
    --model claude-sonnet-4-6 --effort max \
    --judge-model claude-haiku-4-5 \
    --workers 4 \
    --output results/claude-sonnet-4-6-max.json \
    --progress-file results/claude-sonnet-4-6-max.progress.jsonl
```

> `--effort max` is the highest reasoning level the claude CLI exposes. Each probe spawns a fresh `claude -p` session with `--no-session-persistence`, `--disable-slash-commands`, `--tools ""`, and an overriding `--system-prompt`. Same setup as the Opus 4.7 run, just a different model + max thinking.

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 57.1% |
| Raw accuracy | 67.4% |
| **Estimated parameters** | **947B** |
| Effective tier | T5 (deep knowledge — requires frontier-scale models) |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 100% | 200 | 0 | 0 | 200 |
| T2 | 99% | 199 | 1 | 0 | 200 |
| T3 | 88% | 188 | 12 | 0 | 200 |
| T4 | 74% | 173 | 26 | 1 | 200 |
| T5 | 39% | 128 | 50 | 22 | 200 |
| T6 | 0% | 45 | 73 | 82 | 200 |
| T7 | 0% | 11 | 58 | 131 | 200 |

Effective tier: T5 — penalized accuracy 57.1% → estimated 947B parameters on the 89-model open-weight calibration curve.

---

## Observations

### Beats Opus 4.7 — max effort pays off on T3–T5
Sonnet 4.6 at max effort outperforms Opus 4.7 (default effort) by +4.5 percentage points penalized:

| | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|
| Opus 4.7 | 84% | 59% | 25% | 6% | 0% |
| **Sonnet 4.6 max** | **88%** | **74%** | **39%** | 0% | 0% |

The gap is largest on the specialist tiers (T4: +15pp, T5: +14pp). The max-effort thinking budget seems to most help on questions Sonnet *could* know but needs to reason through.

### T6 falls off a cliff — different from Opus's gradual decline
Sonnet 4.6 max collapses at T6 (penalized 0%, 73 wrongs against 45 corrects). Opus 4.7 had a more graceful decline (still 6% at T6 with only 9 wrongs). Two reads:

1. Max-effort thinking encourages Sonnet to commit to plausible-but-wrong answers on long-tail probes — over-confidence as a side effect of extended reasoning.
2. Sonnet 4.6's parametric knowledge simply hits a sharper boundary around 1T-equivalent-tier than Opus 4.7's does.

### Still solidly beaten by gpt-5.5 (any effort)
gpt-5.5 at `low` effort already reaches 67.1% penalized; at `xhigh` it reaches 73.8%. Sonnet 4.6 max at 57.1% sits closer to Opus 4.7 than to either gpt-5.5 configuration on this benchmark.

### Refusal calibration similar to Opus
Sonnet 4.6 max refuses extensively at T5–T7 (235 refusals out of 600 = 39%) — well above gpt-5.5 xhigh's 187 refusals but below Opus 4.7's 466. Refusal-vs-hallucination is mid-range.

---

## Throughput Notes

- 4 workers used (in parallel with two codex runs); higher concurrency would have been fine in isolation.
- Sonnet 4.6 max throughput tracked roughly the same as Opus 4.7 at default effort — claude-cli subprocess startup dominates wallclock more than reasoning-effort selection does.

---

## See Also

- [`claude-opus-4-7.md`](claude-opus-4-7.md) — same script, Opus 4.7 default
- [`gpt-5.5-codex-xhigh.md`](gpt-5.5-codex-xhigh.md) — OpenAI counterpart at highest working effort
- [`../TOOLKIT_AGENT.md`](../TOOLKIT_AGENT.md) — script reference for the Agent path
