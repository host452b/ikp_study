# Benchmark Results: gpt-5.5 (Codex CLI)

**Date:** 2026-05-13
**Notes:** OpenAI ChatGPT-5.5, accessed via the local `codex` CLI in headless mode (`codex exec`). No OpenRouter / external API key — the "model under test" is the ChatGPT Codex subscription itself.
**Environment:** macOS 25.2.0, `codex-cli` 0.125.0, NVIDIA corporate HTTP/HTTPS proxy
**Reasoning effort:** `low` for both query and subject — `minimal` returns empty replies on gpt-5.5; `low` is the cheapest setting that consistently produces an answer
**Judge:** gpt-5.5 at `low` effort (via the same `codex exec` path — self-judge bias acknowledged below)
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)
**Wall time:** ~2 h 35 min @ 8 workers

> Note: `--effort xhigh` was tested first per "best version" intent but proved impractical at ~5 h estimated wall time; `low` keeps the model strong while cutting per-probe time ~5×. Results below are the `low`-effort run.

---

## How to Run

```bash
HTTP_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
HTTPS_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
python scripts/ikp_estimate_codex_cli.py \
    --model gpt-5.5 --effort low \
    --judge-model gpt-5.5 --judge-effort low \
    --workers 8 \
    --output results/gpt-5.5-codex.json \
    --progress-file results/gpt-5.5-codex.progress.jsonl
```

> The script shells out to `codex exec` once per probe with `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, `-c plugins={}`, and `-c service_tier="fast"`. Each invocation is an independent gpt-5.5 session in `/tmp` with no shared context — mirroring how vLLM serves independent requests. Critically, **`-c plugins={}` is required**: without it, codex auto-loads the bundled `superpowers` skill via a shell command at the start of every turn, which contaminates the benchmark and frequently corrupts the final answer.

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 67.1% |
| Raw accuracy | 80.8% |
| **Estimated parameters** | **4.6T** |
| Effective tier | T6 (long-tail knowledge) |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 98% | 198 | 2 | 0 | 200 |
| T2 | 96% | 196 | 4 | 0 | 200 |
| T3 | 86% | 186 | 14 | 0 | 200 |
| T4 | 68% | 166 | 30 | 4 | 200 |
| T5 | 72% | 167 | 24 | 9 | 200 |
| T6 | 50% | 138 | 37 | 25 | 200 |
| T7 | 0% | 80 | 82 | 38 | 200 |

Effective tier: T6 — penalized accuracy 67.1% → estimated 4.6T parameters on the 89-model open-weight calibration curve.

---

## Observations

### Strong knowledge breadth — clear step above Opus 4.7 on this benchmark
gpt-5.5 outperforms Claude Opus 4.7 (penalized 52.6%, 474B estimate) by ~14.5 percentage points overall, with the largest gaps at the harder tiers:

| | T4 | T5 | T6 | T7 (correct) |
|---|---|---|---|---|
| Opus 4.7 | 59% | 25% | 6% | 7/200 |
| gpt-5.5 | 68% | 72% | 50% | 80/200 |

T5 (72% vs 25%) and T6 (50% vs 6%) are the headline wins.

### Different calibration of "I don't know"
At T5–T7 the two models behave very differently:

| | refusals (out of 600) | wrong (out of 600) |
|---|---|---|
| Opus 4.7 | 466 (77.7%) | 44 (7.3%) |
| gpt-5.5 | 72 (12.0%) | 143 (23.8%) |

Opus refuses extensively and rarely hallucinates; gpt-5.5 prefers to take a guess. With the penalized scoring (`wrong = -1.0`, `refusal = 0`), this means **gpt-5.5's raw accuracy advantage (80.8% vs 56.5%) shrinks under the penalty — but it still wins overall** because the extra correct answers outweigh the wrongs. T7 is the only tier where the wrongs (82) outnumber the corrects (80) and gpt-5.5's penalized score collapses to 0.

### Calibration caveat
The 4.6T estimate sits beyond the calibration curve's anchor range (89 open-weight models, 135M–1.6T). The mapping `log10(params_B) = 6.79 × penalized_acc − 0.899` was fit on accuracies up to ~63%; extrapolating to 67.1% yields a multi-trillion number with very wide confidence. Read this as *"what an open-weight model would need to achieve this accuracy if scaling held"*, not as a true parameter count.

---

## Throughput Notes

- 8 workers, ~0.28 probes/s steady-state (≈ 28s per probe combined query + judge).
- Per-probe wallclock is dominated by `codex exec` subprocess startup (~2s) + xhigh-free gpt-5.5 inference (~14s for query at `low`, ~5–8s for judge at `low`).
- Rate dipped to 0.13/s briefly around T6 — likely API-side rate limiting under sustained 8-way concurrency. Recovered on its own.
- `service_tier = "fast"` is enabled in the script; without it the run was ~30% slower in smoke tests.

---

## Methodology Notes (codex specifics)

| Aspect | This run |
|---|---|
| Subject API | Subprocess `codex exec` per probe |
| Judge API | Subprocess `codex exec` per probe (same model, lower effort) |
| System prompt | Prepended to the user prompt (codex has no `--system-prompt` flag) |
| Tools | Sandbox `read-only`; plugins disabled (`-c plugins={}`) so no skill auto-load |
| Session reuse | Fresh `--ephemeral` session per probe; `--ignore-user-config` keeps `~/.codex/config.toml` out of the run |
| Reasoning effort | `low` for both subject and judge (see top note on why not `xhigh`) |

### Self-judge bias
Using gpt-5.5 to grade gpt-5.5 will favour CORRECT verdicts on answers that match the model's own preferred phrasing. Results are directionally valid but cross-model comparison against the Opus 4.7 row (Haiku 4.5 judge) carries a small systematic offset — gpt-5.5's edge would likely shrink by a few points under an independent judge.

### Why query effort dropped from `xhigh` to `low`
`gpt-5.5 + model_reasoning_effort="xhigh"` produces ~100s combined wallclock per probe at 8 workers — projected ~5 h wall time for the full set, with rate limiting making it potentially much longer. Per the user's "fastest form" directive, the run was switched to `low` effort, which on gpt-5.5 is the fastest setting that still produces a non-empty reply (`minimal` returns empty strings).
