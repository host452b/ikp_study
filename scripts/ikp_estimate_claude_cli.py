#!/usr/bin/env python3
"""IKP Estimate via the `claude` CLI (non-networked from the script's POV).

Both the query and the judge go through `claude -p` (Claude Code headless mode)
instead of OpenRouter / vLLM HTTP. Lets us benchmark Claude Code models
(Opus / Sonnet / Haiku) directly on the IKP probe set without an API key.

Usage:
  python scripts/ikp_estimate_claude_cli.py                              # Opus 4.7 default
  python scripts/ikp_estimate_claude_cli.py --model claude-sonnet-4-6
  python scripts/ikp_estimate_claude_cli.py --tiers T4,T5,T6,T7 -w 8

Environment:
  HTTP_PROXY / HTTPS_PROXY are inherited from the parent process and forwarded
  to every `claude -p` subprocess.
"""

import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent / "ikp"
PROBE_FILE = PROJECT_ROOT / "data" / "probes" / "final_probe_set_v8.json"
SYSTEM_MSG = "Answer factual questions directly and concisely. If you don't know, say 'I don't know'."

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_JUDGE_MODEL = "claude-haiku-4-5"
HALLUCINATION_PENALTY = -1.0

# Calibration curve (same as upstream ikp_estimate.py)
CALIB_SLOPE = 6.790
CALIB_INTERCEPT = -0.899
CALIB_N = 89
CALIB_R2 = 0.917

TIER_INFO = {
    "T1": {"range": "< 1B",     "desc": "Universal knowledge — known by the smallest models"},
    "T2": {"range": "1B–7B",    "desc": "Common reference knowledge"},
    "T3": {"range": "7B–32B",   "desc": "Domain-specific knowledge"},
    "T4": {"range": "32B–235B", "desc": "Specialized knowledge"},
    "T5": {"range": "235B–1T",  "desc": "Deep knowledge — requires frontier-scale models"},
    "T6": {"range": "1T–5T",    "desc": "Long-tail knowledge — only the largest models"},
    "T7": {"range": "> 5T",     "desc": "Extreme long-tail — beyond current model capacity"},
}

CLI_PATH = os.environ.get("CLAUDE_CLI", "claude")
SUBPROCESS_TIMEOUT = 180  # seconds per claude -p call


# ── Helpers ────────────────────────────────────────────────────
def strip_thinking(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if cleaned.startswith("<think>"):
        end = cleaned.find("</think>")
        cleaned = cleaned[end + 8:].strip() if end >= 0 else ""
    return cleaned or text


def estimate_params(accuracy: float) -> float:
    if accuracy <= 0:
        return 0
    log_b = CALIB_SLOPE * accuracy + CALIB_INTERCEPT
    return 10 ** log_b


def format_params(b: float) -> str:
    if b <= 0:
        return "N/A"
    if b < 1:
        return f"{b * 1000:.0f}M"
    if b < 1000:
        return f"{b:.0f}B"
    return f"{b / 1000:.1f}T"


def run_claude_cli(prompt: str, model: str, system_prompt: str, effort: str = "") -> dict:
    """Invoke `claude -p` once. Returns parsed JSON result dict or {}."""
    cmd = [
        CLI_PATH, "-p",
        "--model", model,
        "--no-session-persistence",
        "--disable-slash-commands",
        "--tools", "",
        "--system-prompt", system_prompt,
        "--output-format", "json",
    ]
    if effort:
        cmd += ["--effort", effort]
    cmd.append(prompt)
    for attempt in range(3):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT,
                env=os.environ.copy(),
            )
            if proc.returncode != 0:
                # Transient: retry. stderr may contain useful info.
                time.sleep(2 * (attempt + 1))
                continue
            stdout = proc.stdout.strip()
            if not stdout:
                time.sleep(1)
                continue
            # claude -p with --output-format json emits a single JSON object on the
            # last line (status messages may appear before it).
            last = stdout.splitlines()[-1]
            try:
                return json.loads(last)
            except json.JSONDecodeError:
                # Try parsing the whole stdout
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError:
                    time.sleep(1)
                    continue
        except subprocess.TimeoutExpired:
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return {}


# ── Model query ────────────────────────────────────────────────
def make_query_fn(model: str, effort: str = ""):
    def query(question: str) -> tuple[str, float]:
        """Returns (response_text, cost_usd)."""
        data = run_claude_cli(question, model, SYSTEM_MSG, effort)
        if not data:
            return "", 0.0
        cost = float(data.get("total_cost_usd", 0.0) or 0.0)
        if data.get("is_error"):
            return "", cost
        text = data.get("result", "") or ""
        return strip_thinking(text), cost
    return query


# ── Judge ──────────────────────────────────────────────────────
JUDGE_SYSTEM = "You are a strict factual judge. Reply with exactly one of: CORRECT, REFUSAL, or WRONG."


def make_judge_fn(model: str, effort: str = ""):
    def judge(question: str, gold: str, response: str) -> tuple[str, float]:
        if not response or not response.strip():
            return "REFUSAL", 0.0

        if ";" in gold:
            gold_display = " OR ".join(a.strip() for a in gold.split(";"))
            co_note = "\nNOTE: Any of the listed names counts as CORRECT."
        else:
            gold_display = gold
            co_note = ""

        prompt = f"""Classify the model's response.

Question: {question}
Correct answer: {gold_display}
Model's response: {response}

Rules:
1. YEAR must match exactly. 2. NUMBER within 1-2%. 3. NAME: same entity, minor spelling OK.
4. RESEARCH FIELD: accept adjacent/related subfields. Multiple unrelated guesses = WRONG.
5. If refuses or doesn't know: REFUSAL. 6. Different answer: WRONG.
{co_note}
Reply one word: CORRECT, REFUSAL, or WRONG"""

        data = run_claude_cli(prompt, model, JUDGE_SYSTEM, effort)
        cost = float((data or {}).get("total_cost_usd", 0.0) or 0.0)
        if not data:
            return "WRONG", cost
        text = (data.get("result", "") or "").strip().upper()
        # Take only the first word (model sometimes adds explanation)
        first = re.split(r"[\s\n.,!?]", text, maxsplit=1)[0]
        if first.startswith("CORRECT"):
            return "CORRECT", cost
        if first.startswith("REFUSAL"):
            return "REFUSAL", cost
        return "WRONG", cost
    return judge


# ── Display ────────────────────────────────────────────────────
VERDICT_COLORS = {
    "CORRECT": "\033[92m",
    "WRONG": "\033[91m",
    "REFUSAL": "\033[93m",
}
RESET = "\033[0m"
DIM = "\033[90m"


def display_results(model_name: str, results: list, tier_accs: dict, accuracy: float,
                    raw_accuracy: float, estimated_B: float, total_cost: float, inspect: bool):
    print()
    print(f"  ╔══════════════════════════════════════════════════════════╗")
    print(f"  ║  IKP Estimation Results (via claude CLI)                 ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║  Model:     {model_name:42s}  ║")
    print(f"  ║  Probes:    {len(results):<42d}  ║")
    print(f"  ║  Accuracy:  {accuracy:.1%} (penalized)  {raw_accuracy:.1%} (raw){' ' * 14}  ║")
    print(f"  ║  Estimated: {format_params(estimated_B):>6s} parameters{' ' * 26}  ║")
    print(f"  ║  Cost:      ${total_cost:<41.2f}  ║")
    print(f"  ╚══════════════════════════════════════════════════════════╝")

    print(f"\n  {'Tier':<5} {'Accuracy':>9} {'Correct':>8} {'Wrong':>7} {'Refuse':>7} {'Total':>6}  Description")
    print(f"  {'─' * 80}")
    for t in ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]:
        tier_results = [r for r in results if r["tier"] == t]
        if not tier_results:
            continue
        correct = sum(1 for r in tier_results if r["verdict"] == "CORRECT")
        wrong = sum(1 for r in tier_results if r["verdict"] == "WRONG")
        refusal = sum(1 for r in tier_results if r["verdict"] == "REFUSAL")
        total = len(tier_results)
        acc = tier_accs.get(t, 0)
        info = TIER_INFO.get(t, {})
        marker = " ◀ frontier" if acc > 0 and t in ["T5", "T6", "T7"] else ""
        print(f"  {t:<5} {acc:>8.0%} {correct:>8} {wrong:>7} {refusal:>7} {total:>6}  "
              f"{DIM}{info.get('range', '')}: {info.get('desc', '')}{RESET}{marker}")

    effective_tier = "T1"
    for t in ["T7", "T6", "T5", "T4", "T3", "T2", "T1"]:
        if tier_accs.get(t, 0) > 0.05:
            effective_tier = t
            break

    print(f"\n  Effective tier: {effective_tier} ({TIER_INFO[effective_tier]['desc']})")
    print(f"  Estimated size: {format_params(estimated_B)} "
          f"(calibrated on {CALIB_N} open models, R²={CALIB_R2:.3f})")
    print()

    if inspect:
        print(f"  {'─' * 90}")
        print(f"  DETAILED RESULTS")
        print(f"  {'─' * 90}")
        for t in ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]:
            tier_results = [r for r in results if r["tier"] == t]
            if not tier_results:
                continue
            print(f"\n  {DIM}── {t} ──{RESET}")
            for r in tier_results:
                color = VERDICT_COLORS.get(r["verdict"], "")
                symbol = {"CORRECT": "✓", "WRONG": "✗", "REFUSAL": "?"}.get(r["verdict"], "-")
                print(f"  {color}{symbol}{RESET} Q: {r['question']}")
                print(f"    Gold: {r['gold_answer']}")
                if r["response"]:
                    print(f"    Model: {r['response']}")
                print(f"    Verdict: {color}{r['verdict']}{RESET}")
                print()


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="IKP Estimate via the `claude` CLI (non-networked)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    model_group = parser.add_argument_group("Model")
    model_group.add_argument("--model", "-m", metavar="MODEL", default=DEFAULT_MODEL,
                             help=f"Model under test (default: {DEFAULT_MODEL})")
    model_group.add_argument("--effort", metavar="LEVEL", default="",
                             help="Subject reasoning effort: low/medium/high/xhigh/max (default: claude's own default for the alias)")

    eval_group = parser.add_argument_group("Evaluation")
    eval_group.add_argument("--sample", "-n", type=int, metavar="N",
                            help="Sample N probes (default: use all 1400)")
    eval_group.add_argument("--tiers", metavar="TIERS",
                            help="Comma-separated tiers, e.g. T4,T5,T6,T7 (default: all)")
    eval_group.add_argument("--workers", "-w", type=int, default=8,
                            help="Parallel workers (default: 8)")
    eval_group.add_argument("--sequential", "-s", action="store_true",
                            help="Disable parallelism")
    eval_group.add_argument("--output", "-o", metavar="FILE",
                            help="Save detailed results to JSON file")
    eval_group.add_argument("--progress-file", metavar="FILE",
                            help="Append per-probe progress to FILE for live tailing")

    judge_group = parser.add_argument_group("Judge")
    judge_group.add_argument("--judge-model", metavar="MODEL", default=DEFAULT_JUDGE_MODEL,
                             help=f"Judge model (default: {DEFAULT_JUDGE_MODEL})")
    judge_group.add_argument("--judge-effort", metavar="LEVEL", default="",
                             help="Judge reasoning effort (default: claude's own default)")

    display_group = parser.add_argument_group("Display")
    display_group.add_argument("--inspect", action="store_true",
                               help="Show detailed per-probe results")
    display_group.add_argument("--inspect-probes", action="store_true",
                               help="Inspect the probe set and exit")

    args = parser.parse_args()

    probes = json.load(open(PROBE_FILE))

    if args.inspect_probes:
        from collections import Counter
        tier_counts = Counter(p["tier"] for p in probes)
        print(f"\n  IKP Probe Set v8: {len(probes)} probes")
        for t in sorted(tier_counts):
            print(f"    {t}: {tier_counts[t]:>4} probes")
        return

    if args.tiers:
        tier_filter = [t.strip().upper() for t in args.tiers.split(",")]
        probes = [p for p in probes if p["tier"] in tier_filter]
        if not probes:
            print(f"Error: no probes found for tiers {tier_filter}. Valid: T1..T7")
            sys.exit(1)

    if args.sample:
        per_tier = max(args.sample // 7, 1)
        sampled = []
        for t in ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]:
            tier_probes = [p for p in probes if p["tier"] == t]
            sampled.extend(random.sample(tier_probes, min(per_tier, len(tier_probes))))
        probes = sampled

    eff_label = f" effort={args.effort}" if args.effort else ""
    print(f"\n  Testing {args.model}{eff_label} via `claude -p`...")
    query_fn = make_query_fn(args.model, args.effort)
    test_resp, _test_cost = query_fn("What is the capital of France?")
    if not test_resp:
        print(f"  Error: claude CLI returned empty response. Check `claude auth status`.")
        sys.exit(1)
    if "paris" not in test_resp.lower():
        print(f"  Warning: unexpected test response: {test_resp[:100]}")
    else:
        print(f"  Model OK: {test_resp[:60]}")

    je_label = f" effort={args.judge_effort}" if args.judge_effort else ""
    print(f"  Judge:   {args.judge_model}{je_label} (via claude -p)")
    judge_fn = make_judge_fn(args.judge_model, args.judge_effort)

    total = len(probes)
    print(f"\n  Running {total} probes ({args.workers} workers)...\n")

    results = []
    _lock = threading.Lock()
    _done = [0]
    _cost = [0.0]
    _start = time.time()
    progress_fh = open(args.progress_file, "a") if args.progress_file else None

    def eval_one(probe):
        q = probe["question"]
        gold = probe["answer"]
        response, q_cost = query_fn(q)
        verdict, j_cost = judge_fn(q, gold, response)

        with _lock:
            _done[0] += 1
            _cost[0] += q_cost + j_cost
            elapsed = time.time() - _start
            rate = _done[0] / elapsed if elapsed else 0
            eta = (total - _done[0]) / rate if rate else 0
            correct_so_far = sum(1 for r in results if r.get("verdict") == "CORRECT") + (
                1 if verdict == "CORRECT" else 0
            )
            if _done[0] % 5 == 0 or _done[0] == total:
                sys.stderr.write(
                    f"\r  [{_done[0]}/{total}] correct={correct_so_far}  "
                    f"rate={rate:.2f}/s  ETA={eta/60:.1f}min  ${_cost[0]:.2f}   "
                )
                sys.stderr.flush()

            row = {
                "probe_id": probe.get("id", ""),
                "tier": probe["tier"],
                "domain": probe.get("domain", ""),
                "question": q,
                "gold_answer": gold,
                "response": (response or "")[:500],
                "verdict": verdict,
                "query_cost_usd": q_cost,
                "judge_cost_usd": j_cost,
            }
            if progress_fh:
                progress_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                progress_fh.flush()
            return row

    workers = 1 if args.sequential else args.workers
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(eval_one, p): p for p in probes}
        for future in as_completed(futures):
            results.append(future.result())

    sys.stderr.write("\r" + " " * 80 + "\r")
    sys.stderr.flush()
    if progress_fh:
        progress_fh.close()

    tier_stats = defaultdict(lambda: {"correct": 0, "total": 0, "refusal": 0, "wrong": 0})
    for r in results:
        t = r["tier"]
        tier_stats[t]["total"] += 1
        if r["verdict"] == "CORRECT":
            tier_stats[t]["correct"] += 1
        elif r["verdict"] == "REFUSAL":
            tier_stats[t]["refusal"] += 1
        else:
            tier_stats[t]["wrong"] += 1

    tier_accs = {}
    for t in ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]:
        s = tier_stats[t]
        if s["total"] > 0:
            score = (s["correct"] + HALLUCINATION_PENALTY * s["wrong"]) / s["total"]
            tier_accs[t] = max(score, 0.0)
        else:
            tier_accs[t] = 0.0

    tested_accs = [tier_accs[t] for t in tier_accs if tier_stats[t]["total"] > 0]
    accuracy = sum(tested_accs) / len(tested_accs) if tested_accs else 0
    correct_total = sum(s["correct"] for s in tier_stats.values())
    raw_accuracy = correct_total / len(results) if results else 0
    estimated_B = estimate_params(accuracy)

    display_results(args.model, results, tier_accs, accuracy, raw_accuracy,
                    estimated_B, _cost[0], args.inspect)

    if args.output:
        output = {
            "model": args.model,
            "judge_model": args.judge_model,
            "via": "claude-cli",
            "probes_used": len(results),
            "accuracy": accuracy,
            "raw_accuracy": raw_accuracy,
            "estimated_params_B": estimated_B,
            "total_cost_usd": _cost[0],
            "tier_accuracy": tier_accs,
            "tier_stats": {k: dict(v) for k, v in tier_stats.items()},
            "calibration": {
                "slope": CALIB_SLOPE,
                "intercept": CALIB_INTERCEPT,
                "n_models": CALIB_N,
                "r_squared": CALIB_R2,
            },
            "results": results,
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"  Results saved to {args.output}")


if __name__ == "__main__":
    main()
