# IKP Estimation Toolkit — Agent path

> **Two paths, two toolkits.** This file covers the **Agent path** — driving a
> headless coding-agent CLI (one subprocess per probe) instead of an HTTP API.
> Two CLIs are supported, with one script each:
>
> | CLI | Script | Logged-in model |
> |---|---|---|
> | `claude -p` (Anthropic Claude Code) | `scripts/ikp_estimate_claude_cli.py` | claude-opus-4-7 / sonnet / haiku |
> | `codex exec` (OpenAI Codex CLI) | `scripts/ikp_estimate_codex_cli.py` | gpt-5.5 (and other ChatGPT-backed models) |
>
> For evaluating an OpenAI-compatible HTTP endpoint (vLLM, llama.cpp, Ollama, OpenRouter),
> use the HTTP API path in [`TOOLKIT.md`](TOOLKIT.md).

## When to use this path

- You want to benchmark a model exposed through a coding-agent subscription (Claude Code or ChatGPT Codex) without obtaining an API key for the underlying provider.
- You don't want to (or can't) stand up an HTTP inference server.
- Each probe spawns a fresh CLI subprocess so probes do not share context — this mirrors how vLLM serves stateless HTTP requests.

---

## Variant 1 — Claude Code (`claude -p`)

### One-liner

```bash
python scripts/ikp_estimate_claude_cli.py \
    --model claude-opus-4-7 \
    --judge-model claude-haiku-4-5 \
    --workers 8 \
    --output results/claude-opus-4-7-claude-cli.json
```

Proxy env (`HTTP_PROXY` / `HTTPS_PROXY`) is inherited into every `claude -p` subprocess.

### CLI reference

| Flag | Default | Purpose |
|---|---|---|
| `--model, -m MODEL` | `claude-opus-4-7` | Subject model (any alias `claude --model` accepts). |
| `--judge-model MODEL` | `claude-haiku-4-5` | Judge model — Haiku avoids self-judging bias against Opus. |
| `--sample, -n N` | all 1400 | Stratified random sample: `N/7` per tier. |
| `--tiers TIERS` | all 7 | Comma-separated tiers, e.g. `T4,T5,T6,T7`. |
| `--workers, -w N` | 8 | Parallel subprocess workers. 4–16 reasonable on Power Users. |
| `--sequential, -s` | off | Force `workers=1`. |
| `--output, -o FILE` | — | Write per-probe results + tier stats to JSON. |
| `--progress-file FILE` | — | Append every completed probe as one JSON line. |
| `--inspect` | off | Print per-probe details after scoring. |
| `--inspect-probes` | off | Print probe set per tier and exit. |

### Under the hood

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

- `--system-prompt` **replaces** Claude Code's default system prompt with the IKP factual prompt.
- `--tools ""` and `--disable-slash-commands` keep the model on its parametric knowledge — no skills, no plugins, no tools.
- `--no-session-persistence` avoids writing transcript state to disk.
- `--output-format json` returns a single JSON object; the script extracts `result` as the answer.

### Caveats (Claude variant)

- ~1–2 s Node + Claude Code subprocess startup per probe. 8 workers ≈ 0.6 probes/s wall-clock (≈ 35–40 min for 1400 probes).
- No `--thinking` flag — reasoning effort is whatever the Claude Code default for the alias is. To toggle thinking mode, edit `run_claude_cli`.

---

## Variant 2 — ChatGPT Codex (`codex exec`)

### One-liner

```bash
python scripts/ikp_estimate_codex_cli.py \
    --model gpt-5.5 --effort low \
    --judge-model gpt-5.5 --judge-effort low \
    --workers 8 \
    --output results/gpt-5.5-codex.json
```

Proxy env is inherited. Codex is logged in via your ChatGPT account (`codex login status`).

### CLI reference

| Flag | Default | Purpose |
|---|---|---|
| `--model, -m MODEL` | `gpt-5.5` | Subject model (any alias `codex -m` accepts). |
| `--effort LEVEL` | `xhigh` | `model_reasoning_effort`. **`minimal` is broken on gpt-5.5 (empty replies)**; `low` is the practical floor; `xhigh` is the "best version" but ~5× slower wall-clock. |
| `--judge-model MODEL` | `gpt-5.5` | Judge model. |
| `--judge-effort LEVEL` | `low` | Reasoning effort for the judge. `low` is fast and reliable. |
| `--sample, -n N` | all 1400 | Stratified random sample. |
| `--tiers TIERS` | all 7 | Comma-separated tier filter. |
| `--workers, -w N` | 4 | Default lower than the Claude variant — codex calls are ~3× slower. 8 still works but rate-limit dips at sustained concurrency. |
| `--sequential, -s` | off | Force `workers=1`. |
| `--output, -o FILE` | — | JSON dump of full results. |
| `--progress-file FILE` | — | JSONL stream of per-probe results. |

### Under the hood

Each probe is one call to:

```bash
codex exec \
    --skip-git-repo-check --ephemeral \
    --ignore-user-config --ignore-rules \
    -C /tmp -s read-only --color never \
    -o <tempfile> \
    -c plugins={} \
    -c service_tier="fast" \
    -m gpt-5.5 -c model_reasoning_effort="low" \
    "<IKP system prompt>\n\nQuestion: <probe>"
```

- The IKP system message is **prepended into the user prompt** because `codex exec` has no `--system-prompt` flag.
- `-c plugins={}` is **load-bearing**: without it, codex auto-loads the bundled `superpowers` skill at the start of every turn via a shell command (`sed -n '1,200p' ~/.codex/superpowers/skills/.../SKILL.md`). That contaminates the benchmark and frequently corrupts the final answer with thinking traces like `"W גSomething? Wait final..."`.
- `-c service_tier="fast"` cuts wall time ~30% on smoke tests.
- `--ignore-user-config` + `-C /tmp` + `--ephemeral` ensure no `~/.codex/config.toml`, no local `AGENTS.md`, and no persisted session state leak into the run.
- `-o <tempfile>` collects the final agent message cleanly — stdout `--json` events include thinking chatter we don't want.

### Caveats (Codex variant)

- **`minimal` effort is broken** on gpt-5.5: returns empty replies. The script defaults to `xhigh` per the "best version" intent but in practice you'll usually want `--effort low` for tractable wall time. `xhigh` ≈ 100s combined per probe under 8-way concurrency → ~5 h for 1400 probes; `low` ≈ 28s combined → ~2.5 h.
- **Self-judging bias** — when both `--model` and `--judge-model` are the same, CORRECT verdicts skew up. Use a smaller OpenAI model as judge (e.g. `--judge-model gpt-5.5-mini` once available) or run the judge under the Claude variant for cross-model independence.
- **Rate limiting** shows up as ~0.13 probes/s dips during long T6/T7 stretches at 8 workers. Recovers on its own. Drop to 4–6 workers if you see persistent throttling.
- Same open-weight calibration caveat as the Claude variant — the estimated parameter count is a comparison-by-analogy onto the 89-model open-weight curve, not a true parameter readout.
