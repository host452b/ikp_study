# IKP Project: Deep Analysis

> **[中文版见 PROJECT_ANALYSIS.zh.md]**

---

## 1. What Is This Project?

**IKP (Incompressible Knowledge Probes)** answers one question: **given only black-box API access to an LLM, how many parameters does it have?**

Frontier vendors (OpenAI, Anthropic, Google, etc.) routinely decline to disclose model sizes. IKP provides an empirical, reproducible method to estimate that size from the outside — using the model's own knowledge capacity as a proxy signal.

The core insight is information-theoretic: **factual knowledge is incompressible**. A small model cannot memorize long-tail facts no matter how well it is trained. As parameter count increases log-linearly, so does the breadth of facts the model reliably recalls. IKP exploits this with probes at seven calibrated difficulty tiers, from universal trivia (T1) to extreme long-tail obscurities (T7).

**Key result:** Penalized accuracy on 1,400 probes scales log-linearly with parameter count across 89 open-weight models (135M–1.6T), R² = 0.917.

---

## 2. Core Methodology

### 2.1 Seven Tiers

| Tier | Web Frequency | Parameter Range | Example |
|---|---|---|---|
| T1 | >100K docs | 0.1B–1B | Country capitals, basic science |
| T2 | 10K–100K | 1B–7B | Nobel winners, landmark heights |
| T3 | 1K–10K | 7B–70B | Specific dates, niche researchers |
| T4 | 100–1K | 70B–300B | Minor scientists, niche specs |
| T5 | 10–100 | 300B–1T | Minor entity details, pub metadata |
| T6 | 2–10 | 1T–5T | Obscure researchers, minor workshops |
| T7 | ~1 | >5T | Ceiling / RAG detection |

**Tier assignment** is empirical: test against 6 landmark models (Qwen 2.5 0.5B → Gemini 3.1 Pro). A probe belongs to tier Tk if the Tk landmark is the *smallest* model that answers correctly. Monotonicity violations are discarded.

### 2.2 Scoring

- **3 phrasings per probe**, best answer taken
- **Judge:** Gemini 3 Flash Preview (OpenRouter)
- **Penalized accuracy:** `tier_score = max(0, (correct − wrong) / total)` with HALLUCINATION_PENALTY = −1.0
- **Final accuracy:** mean over tested tiers

### 2.3 Calibration Curve

```
log10(params_B) = 6.790 × accuracy − 0.899
```

R² = 0.917 · LOO median fold error 1.59× · 68.5% within 2× · 87.6% within 3×

**MoE models:** total parameters (R²=0.79) predict accuracy far better than active parameters (R²=0.51).

---

## 3. Complete Workflow

```
Stage 1 (one-time): Probe generation
  01_generate_probes.py → LLM-generated T1–T4
  09_researcher_probes.py → researcher T3–T7
  assemble_final_dataset.py → final_probe_set_v8.json (frozen)

Stage 2 (one-time): Calibration
  02_run_calibration.py + 03_fit_calibration.py → calibration_fit.json

Stage 3 (user path): Estimate a model
  ikp_estimate.py → 1,400 probes → judge → tier scores → log10(P)

Stage 4 (research path): Analysis & paper
  run_all_models.py → 188 models
  generate_figures.py → 9 paper figures
  latexmk main.tex → PDF
```

---

## 4. Key Findings

1. **Log-linear scaling law** — factual accuracy ↔ log(parameters), R²=0.917 across 4 orders of magnitude
2. **Total > active params for MoE** — knowledge capacity depends on total weights, not active experts per token
3. **Thinking modes: modest gain** — chain-of-thought helps T3–T5 (inference needed) more than T6–T7 (pure recall)
4. **Hallucination fingerprinting** — models from the same training lineage hallucinate on the *same* T5–T6 probes (Jaccard similarity detects shared training data)
5. **Densing Law falsified** — no statistically significant knowledge increase over time after controlling for parameter count
6. **Researcher recognition ∝ citations** — Spearman ρ = 0.575 between citation count and recognition rate

---

## 5. Practical Uses

| Use case | How |
|---|---|
| Estimate closed-source model size | Run `ikp_estimate.py` against the API |
| Detect silent model swaps at an endpoint | Weekly IKP run; accuracy drop → smaller model |
| Benchmark local / quantized models | `--api-base localhost --tiers T4,T5,T6,T7` |
| Measure knowledge loss from fine-tuning | Before/after IKP; per-tier comparison |
| Detect RAG / external retrieval | Unexpectedly high T7 score = likely retrieval-augmented |
| Detect model lineage / distillation | Jaccard similarity of wrong-answer sets |

---

## 6. Extension Opportunities

- **Multilingual IKP** — Chinese/Japanese/Arabic probes; `08_chinese_probes.py` is a starter
- **Domain-specific calibration curves** — per-domain fits to detect specialization
- **Temporal recalibration** — periodic refit on new open-weight cohort
- **Integration with leaderboards** — IKP knowledge-breadth dimension for HF Open LLM Leaderboard
- **Multimodal probes** — visual knowledge tiers for VLMs
- **Adversarial probes** — false-memory probes to measure over-confidence

---

## 7. Architecture

```
User
 │ python scripts/ikp_estimate.py --model X
 ▼
Estimation Pipeline
 ├── Load probes      data/probes/final_probe_set_v8.json
 ├── Query model      src/api_client.py (async, 16 workers)
 ├── Collect answers  src/probe_runner.py (3 phrasings)
 ├── Judge            src/scorer.py → Gemini 3 Flash
 ├── Score            src/calibration.py (penalized accuracy)
 └── Estimate         log10(P) = 6.790 × acc − 0.899
 ▼
Parameter estimate + per-tier breakdown
```

---

## 8. Quick Reference

| Goal | Command |
|---|---|
| Estimate a model | `python scripts/ikp_estimate.py -m openai/gpt-4.1` |
| Fast estimate (~1 min) | `... --sample 200` |
| Local model, hard tiers only | `... --api-base http://localhost:8000/v1 --api-key EMPTY --tiers T4,T5,T6,T7` |
| Thinking mode | `... --thinking` |
| Export to JSON | `... -o out.json` |
| View calibration curve | `... --show-calibration` |
| Browse probe set | `... --inspect-probes` |
| Lookup a researcher | `python -m cli research --researcher "NAME"` |
| Re-score a probe | `python -m cli eval IKP_T5_0123` |
| Batch all models | `python scripts/run_all_models.py --skip-existing` |
| Regenerate figures | `python paper/figures/generate_figures.py` |
| Rebuild PDF | `cd paper && latexmk -pdf main.tex` |
