# IKP Estimation Toolkit (ikp_study overlay)

This document covers `scripts/ikp_estimate.py` in **this repo** (`ikp_study/`),
which extends the upstream [`ikp/scripts/ikp_estimate.py`](ikp/TOOLKIT.md) with:

- `--tiers` — run only a subset of the 7 tiers
- Auto-resolved data path into the `ikp/` submodule

For the original upstream CLI reference, see [`ikp/TOOLKIT.md`](ikp/TOOLKIT.md).

## One-liner

```bash
export OPENROUTER_API_KEY=sk-or-...
python scripts/ikp_estimate.py --model openai/gpt-4.1
```

## CLI reference

All flags from the upstream script are supported. The additions are:

### Evaluation

| Flag | Default | Purpose |
|---|---|---|
| `--sample, -n N` | all 1400 | Stratified random sample: `N/7` probes per tier. |
| `--tiers TIERS` | all 7 | Comma-separated tiers to run, e.g. `T4,T5,T6,T7`. Accuracy is averaged over tested tiers only. |
| `--workers, -w N` | 16 | Parallel requests. |
| `--sequential, -s` | off | Force `workers=1`. |
| `--output, -o FILE` | — | Dump full per-probe results + calibration metadata to JSON. |

### Model

| Flag | Default | Purpose |
|---|---|---|
| `--model, -m MODEL` | — | Target model ID, e.g. `openai/gpt-4.1`. |
| `--api-base URL` | `https://openrouter.ai/api/v1` | Any OpenAI-compatible endpoint. |
| `--api-key KEY` | `$OPENROUTER_API_KEY` | Bearer token for `--api-base`. |
| `--thinking` | off | Pass `reasoning: {"effort":"medium"}` to the model. |

### Inspection / info

| Flag | Purpose |
|---|---|
| `--inspect` | Print every probe with model answer, gold, and verdict after scoring. |
| `--inspect-probes` | Print the probe set by tier and exit (no API call). |
| `--show-calibration` | Print calibration formula, reference points, and R². |

## Testing local / quantized models on hard tiers (T4–T7)

### Supported local inference servers

| Server | Default API base | Example launch |
|---|---|---|
| **vLLM** | `http://localhost:8000/v1` | `vllm serve ./model --port 8000` |
| **llama.cpp server** | `http://localhost:8080/v1` | `./llama-server -m model.gguf --port 8080` |
| **Ollama** | `http://localhost:11434/v1` | `ollama serve` |
| **LM Studio** | `http://localhost:1234/v1` | start from the UI |

`OPENROUTER_API_KEY` is always required (for the Gemini judge).
Judge cost for a T4–T7 run: roughly **$0.05–0.20**.

### Single model, T4–T7 only

```bash
export OPENROUTER_API_KEY=sk-or-...

python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model-name \
    --tiers    T4,T5,T6,T7
```

Add `--sample 280` to run 70 probes per tier (~3× faster):

```bash
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model-name \
    --tiers    T4,T5,T6,T7 \
    --sample   280 \
    --output   results/my-model.json
```

### Batch: compare multiple quantizations

```bash
#!/bin/bash
# test_local_models.sh
export OPENROUTER_API_KEY=sk-or-...

MODELS=(
  "Qwen3-30B-A3B-Q4"
  "Qwen3-30B-A3B-Q8"
  "Llama-3-70B-Q4_K_M"
  "Llama-3-70B-Q8_0"
)

mkdir -p results/local_quant

for MODEL in "${MODELS[@]}"; do
    echo "=== $MODEL ==="
    python scripts/ikp_estimate.py \
        --api-base http://localhost:8000/v1 \
        --api-key  EMPTY \
        --model    "$MODEL" \
        --tiers    T4,T5,T6,T7 \
        --output   "results/local_quant/${MODEL}.json"
done
```

> The model name must match what the inference server exposes —
> vLLM uses `--served-model-name`; Ollama uses the model tag.

### Quick preview before spending tokens

```bash
# Browse T4–T7 sample questions
python scripts/ikp_estimate.py --inspect-probes | grep -A4 "── T4 ──" | head -20

# Tiny sample with per-probe output (8 probes per tier)
python scripts/ikp_estimate.py \
    --api-base http://localhost:8000/v1 \
    --api-key  EMPTY \
    --model    my-model \
    --tiers    T4,T5,T6,T7 \
    --sample   56 \
    --inspect
```

### Interpreting partial-tier results

When `--tiers` is used, the parameter estimate is the calibration curve
applied to the **mean of the tested tiers only** — not a full 7-tier
average. Use the number for **relative ranking** across your own model
variants, not as a ground-truth size claim.
