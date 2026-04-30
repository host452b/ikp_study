# IKP Project: Deep Analysis

> **[中文版见 PROJECT_ANALYSIS.zh.md]**
>
> Upstream project: [19PINE-AI/ikp](https://github.com/19PINE-AI/ikp) (in `ikp/` submodule)

---

## 1. What Is This Project?

**IKP (Incompressible Knowledge Probes)** answers one question: **given only black-box API access to an LLM, how many parameters does it have?**

Frontier vendors (OpenAI, Anthropic, Google, etc.) routinely decline to disclose model sizes. IKP provides an empirical, reproducible method to estimate that size from the outside — using the model's own knowledge capacity as a proxy signal.

**Core insight:** Factual knowledge is incompressible. A small model cannot memorize long-tail facts no matter how well it is trained. As parameter count increases, so does the breadth of facts the model reliably recalls. IKP exploits this with probes at seven calibrated difficulty tiers.

**Key result:** R² = 0.917 across 89 open-weight models (135M–1.6T).

---

## 2. Core Methodology

### Seven Tiers

| Tier | Web Frequency | Parameter Range | Example |
|---|---|---|---|
| T1 | >100K docs | 0.1B–1B | Country capitals, basic science |
| T2 | 10K–100K | 1B–7B | Nobel winners, landmark heights |
| T3 | 1K–10K | 7B–70B | Specific dates, niche researchers |
| T4 | 100–1K | 70B–300B | Minor scientists, niche specs |
| T5 | 10–100 | 300B–1T | Minor entity details, pub metadata |
| T6 | 2–10 | 1T–5T | Obscure researchers, minor workshops |
| T7 | ~1 | >5T | Ceiling / RAG detection |

**Tier assignment:** empirically calibrated against 6 landmark models (Qwen 2.5 0.5B → Gemini 3.1 Pro). A probe belongs to tier Tk if Tk is the smallest landmark that answers correctly.

### Calibration Curve

```
log10(params_B) = 6.790 × penalized_accuracy − 0.899
```

- R² = 0.917  ·  LOO median fold error 1.59×  ·  68.5% within 2×  ·  87.6% within 3×
- **MoE:** total parameters (R²=0.79) >> active parameters (R²=0.51)

### Scoring

- 3 phrasings per probe, best taken
- Judge: Gemini 3 Flash Preview (OpenRouter)
- Penalized: `tier_score = max(0, (correct − wrong) / total)`, WRONG = −1.0
- Final accuracy = mean over tested tiers

---

## 3. Complete Workflow

```
Stage 1 — Probe generation (one-time, frozen)
  01_generate_probes.py + 09_researcher_probes.py
  → final_probe_set_v8.json (1,400 probes)

Stage 2 — Calibration (one-time)
  02_run_calibration.py + 03_fit_calibration.py
  → calibration_fit.json

Stage 3 — Estimate a model (user path)
  scripts/ikp_estimate.py
  → load probes → query model (16 workers) → judge → tier scores → log10(P)

Stage 4 — Research / paper path
  run_all_models.py (188 models) → generate_figures.py → latexmk
```

---

## 4. Key Findings

1. **Log-linear scaling law** — R²=0.917 across 4 orders of magnitude
2. **MoE total > active params** — knowledge capacity tracks total weight count
3. **Thinking: modest gain** — helps T3–T5 (inference), less so T6–T7 (pure recall)
4. **Hallucination fingerprinting** — Jaccard similarity of wrong-answer sets detects shared training data and model lineage
5. **Densing Law falsified** — no significant knowledge increase over time after controlling for params
6. **Researcher recognition ∝ citations** — Spearman ρ = 0.575

---

## 5. Practical Uses

| Use case | How |
|---|---|
| Estimate closed-source model size | `ikp_estimate.py` against the API |
| Detect silent endpoint model swap | Weekly IKP run; accuracy drop = smaller model |
| Benchmark local / quantized models | `--tiers T4,T5,T6,T7 --api-base localhost` |
| Measure fine-tuning knowledge loss | Before/after comparison, per-tier breakdown |
| Detect RAG / retrieval augmentation | High T7 score = likely retrieval-augmented |
| Detect model lineage / distillation | Jaccard similarity of wrong-answer sets |

---

## 6. Extension Opportunities

- **Multilingual IKP** — Chinese/Japanese/Arabic probes (`08_chinese_probes.py` as starter)
- **Domain-specific calibration curves** — per-domain fits for specialization detection
- **Temporal recalibration** — periodic refit on new open-weight cohort
- **Leaderboard integration** — knowledge-breadth dimension for HF Open LLM Leaderboard
- **Multimodal probes** — visual knowledge tiers for VLMs
- **Adversarial probes** — false-memory probes to measure over-confidence
- **Continuous endpoint monitoring** — detect silent model swaps at vendor APIs

---

## 7. Quick Reference

| Goal | Command (from `ikp_study/` root) |
|---|---|
| Estimate a model | `python scripts/ikp_estimate.py -m openai/gpt-4.1` |
| Fast estimate | `... --sample 200` |
| Local model, hard tiers | `... --api-base http://localhost:8000/v1 --api-key EMPTY --tiers T4,T5,T6,T7` |
| With thinking | `... --thinking` |
| Export to JSON | `... -o out.json` |
| View calibration | `... --show-calibration` |
| Browse probes | `... --inspect-probes` |
| Upstream CLI (no --tiers) | `python ikp/scripts/ikp_estimate.py -m MODEL` |
| Upstream interactive CLI | `cd ikp && python -m cli research --researcher "NAME"` |
| Batch all models | `cd ikp && python scripts/run_all_models.py --skip-existing` |
| Regenerate figures | `cd ikp && python paper/figures/generate_figures.py` |
