# Benchmark Results: claude-opus-4-7 (Claude Code, 1M context)

**Date:** 2026-05-13
**Notes:** Anthropic Claude Opus 4.7, accessed via the local `claude` CLI in headless mode (`claude -p`). No vLLM / OpenRouter / external API key — the "model under test" is the Claude Code subscription itself.
**Environment:** macOS 25.2.0, `claude` CLI 2.1.140, NVIDIA corporate HTTP/HTTPS proxy
**Judge:** `claude-haiku-4-5` (also via `claude -p`) — independent from the subject model, avoids self-judging bias
**Probes:** IKP probe set v8, 1,400 probes × 7 tiers (T1–T7)
**Wall time:** ~37 min

---

## How to Run

```bash
HTTP_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
HTTPS_PROXY=http://kix01nvproxy11.nvidia.com:3128 \
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 \
    --judge-model claude-haiku-4-5 \
    --workers 8 \
    --output results/claude-opus-4-7-claude-cli.json \
    --progress-file results/claude-opus-4-7-claude-cli.progress.jsonl
```

> The script shells out to `claude -p` once per probe with `--no-session-persistence`, `--disable-slash-commands`, `--tools ""`, and an overriding `--system-prompt` matching the original IKP system message. Each invocation is an independent Opus 4.7 session — no shared context across probes, mirroring how vLLM serves independent requests.

---

## Results

| Metric | Value |
|---|---|
| Penalized accuracy | 52.6% |
| Raw accuracy | 56.5% |
| **Estimated parameters** | **474B** |
| Effective tier | T6 (long-tail knowledge) |
| Refusal rate (T5–T7 avg) | 77.7% |
| Wrong rate (T5–T7 avg) | 7.3% |

| Tier | Accuracy | Correct | Wrong | Refuse | Total |
|---|---|---|---|---|---|
| T1 | 100% | 200 | 0 | 0 | 200 |
| T2 | 95% | 195 | 5 | 0 | 200 |
| T3 | 84% | 175 | 8 | 17 | 200 |
| T4 | 59% | 131 | 13 | 56 | 200 |
| T5 | 25% | 62 | 12 | 126 | 200 |
| T6 | 6% | 21 | 9 | 170 | 200 |
| T7 | 0% | 7 | 23 | 170 | 200 |

Effective tier: T6 — penalized accuracy 52.6% → estimated 474B parameters on the 89-model open-weight calibration curve.

---

## Observations

### Strong refusal calibration
Opus 4.7 refuses far more often than it hallucinates on hard probes: at T5–T7 it refused 466 out of 600 (77.7%) but only got 44 wrong (7.3%). This is in stark contrast to mid-tier Qwen3 models in this repo, which produce hundreds of confident wrong answers at the same tiers. The penalized accuracy benefits enormously from this — wrongs cost 1.0 each while refusals cost 0.

### Effective tier reaches T6
The estimator's "effective tier" jumps from T4/T5 for Qwen-family models in this repo to **T6** for Opus 4.7. The only other model in `benchmark.csv` to register meaningful T5 accuracy is DeepSeek-V4-Flash (21% T5, 0% T6), placing Opus 4.7 a clear step above on this benchmark.

### Calibration caveat
The 474B estimate is anchored on a curve fit to **open-weight** models ranging 135M–1.6T. The mapping `log10(params_B) = 6.79 × penalized_acc − 0.899` assumes the test model's accuracy/size relationship follows the same scaling law as Qwen/Llama/DeepSeek. Closed proprietary models may break this assumption — Anthropic has not disclosed Opus 4.7's parameter count, so this number is a comparison-by-analogy, not a true parameter readout. The "what an open model would need to achieve this accuracy" framing is the right reading.

---

## Throughput Notes

- 8 workers held steady at 0.62–0.66 probes/s (≈ 12–13s per probe end-to-end including `claude -p` subprocess startup).
- No rate limit hits with the Power Users subscription at this concurrency level.

---

## Methodology Differences from Upstream

| Aspect | Upstream `ikp_estimate.py` | This run (`ikp_estimate_claude_cli.py`) |
|---|---|---|
| Subject API | HTTP to OpenRouter / vLLM | Subprocess `claude -p` per probe |
| Judge API | OpenRouter Gemini 3 Flash | Subprocess `claude -p` Haiku 4.5 |
| System prompt | Sent in payload | `--system-prompt` flag (overrides Claude Code default) |
| Tools/skills | N/A | Disabled via `--tools ""` and `--disable-slash-commands` |
| Session reuse | One HTTP client | Fresh process & session per probe |

The "fresh process per probe" pattern means each query sees a clean Opus 4.7 with no carryover — equivalent to how vLLM serves stateless requests. This is the closest non-API analog to the upstream methodology while routing entirely through the Claude Code subscription.
