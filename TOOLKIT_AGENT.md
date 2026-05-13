# IKP Estimation Toolkit — Agent path (`claude -p`)

> **Two paths, two toolkits.** This file covers the **Agent path** —
> `scripts/ikp_estimate_claude_cli.py`, which shells out to the local
> `claude` CLI in headless mode (one `claude -p` invocation per probe).
>
> For evaluating an OpenAI-compatible HTTP endpoint (vLLM, llama.cpp,
> Ollama, OpenRouter), use the HTTP API path in
> [`TOOLKIT.md`](TOOLKIT.md).

## When to use this path

- You want to benchmark a Claude Code model (Opus / Sonnet / Haiku) on IKP.
- You have an active `claude` CLI login but no Anthropic API key.
- You don't want to (or can't) stand up an HTTP inference server.

The "model under test" is the Claude Code subscription itself. Each probe
spawns a fresh `claude -p` subprocess, so probes do not share context —
this mirrors how vLLM serves stateless HTTP requests.

## One-liner

```bash
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 \
    --judge-model claude-haiku-4-5 \
    --workers 8 \
    --output results/claude-opus-4-7-claude-cli.json
```

If you're behind a corporate proxy:

```bash
HTTP_PROXY=http://proxy.example.com:3128 \
HTTPS_PROXY=http://proxy.example.com:3128 \
python scripts/ikp_estimate_claude_cli.py --model claude-opus-4-7
```

Proxy env vars are forwarded into every `claude -p` subprocess.

## CLI reference

### Model

| Flag | Default | Purpose |
|---|---|---|
| `--model, -m MODEL` | `claude-opus-4-7` | Subject model name (any alias accepted by `claude --model`). |
| `--judge-model MODEL` | `claude-haiku-4-5` | Judge model (also called via `claude -p`). Haiku is independent from Opus and avoids self-judging bias. |

### Evaluation

| Flag | Default | Purpose |
|---|---|---|
| `--sample, -n N` | all 1400 | Stratified random sample: `N/7` probes per tier. |
| `--tiers TIERS` | all 7 | Comma-separated tiers, e.g. `T4,T5,T6,T7`. |
| `--workers, -w N` | 8 | Parallel subprocess workers. 8 is a safe ceiling for the Power Users subscription; 4–16 are reasonable. |
| `--sequential, -s` | off | Force `workers=1`. |
| `--output, -o FILE` | — | Write per-probe results + tier stats to JSON. |
| `--progress-file FILE` | — | Append every completed probe as one JSON line — useful for `tail -f` while a long run is in flight. |

### Inspection

| Flag | Purpose |
|---|---|
| `--inspect` | Print every probe with answer, gold, and verdict after scoring. |
| `--inspect-probes` | Print the probe set per tier and exit (no CLI call). |

## Under the hood

Each probe is one call to:

```bash
claude -p \
    --model claude-opus-4-7 \
    --no-session-persistence \
    --disable-slash-commands \
    --tools "" \
    --system-prompt "Answer factual questions directly and concisely. If you don't know, say 'I don't know'." \
    --output-format json \
    "<probe question>"
```

- `--system-prompt` **replaces** Claude Code's default system prompt with the IKP-style factual prompt, matching how the HTTP path sends `SYSTEM_MSG`.
- `--tools ""` and `--disable-slash-commands` disable tools/skills/plugins so the model answers purely from its parametric knowledge.
- `--no-session-persistence` avoids writing transcript state to disk.
- `--output-format json` returns a single JSON object; the script extracts `result` as the model answer.

The judge is the same wrapper with a different system prompt (`JUDGE_SYSTEM`) and the IKP rubric in the user message.

## Caveats

- **Subprocess overhead is real.** Each `claude -p` invocation pays a Node + Claude Code startup tax of ~1–2 s on top of the API call. With 8 workers, expect ~0.6 probes/s wall-clock (≈ 35–40 min for the full 1400-probe set).
- **Calibration curve still uses open-weight anchor models.** The 89-model open-weight calibration applies the same `log10(params_B) = 6.79 · acc − 0.899` mapping. For proprietary Claude models the "estimated parameters" number is best read as *"what an open-weight model would need to achieve this accuracy"* — not as an actual parameter count.
- **No `--thinking` flag.** Reasoning effort is controlled by the model alias and Claude Code defaults; if you want a thinking-mode comparison, pass `--effort` through by editing `run_claude_cli` (or run two configs separately).
