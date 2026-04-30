#!/usr/bin/env python3
"""Export all IKP log results to benchmark.csv (utf-8-sig)."""
import re, csv
from pathlib import Path

# (log_path, short_name, actual_params, vendor, hf_id)
LOG_MAP = [
    ("/tmp/ikp_bf16.log",                        "Qwen2.5-VL-7B-BF16",            "7B",       "Qwen",       "Qwen/Qwen2.5-VL-7B-Instruct"),
    ("/tmp/ikp_full.log",                        "Qwen2.5-VL-7B-FP8",             "7B",       "NVIDIA",     "nvidia/Qwen2.5-VL-7B-Instruct-FP8"),
    ("/tmp/ikp_thinking.log",                    "Qwen2.5-VL-7B-FP8+think",       "7B",       "NVIDIA",     "nvidia/Qwen2.5-VL-7B-Instruct-FP8"),
    ("/tmp/ikp_nvfp4.log",                       "Qwen2.5-VL-7B-NVFP4",           "7B",       "NVIDIA",     "nvidia/Qwen2.5-VL-7B-Instruct-NVFP4"),
    ("/tmp/ikp_14b.log",                         "Qwen2.5-14B-BF16",              "14B",      "Qwen",       "Qwen/Qwen2.5-14B-Instruct"),
    ("/tmp/ikp_Qwen-Qwen3-6-35B-A3B.log",       "Qwen3.6-35B-A3B(MoE)",          "35B/3B",   "Qwen",       "Qwen/Qwen3.6-35B-A3B"),
    ("/tmp/ikp_Qwen-Qwen3-6-35B-A3B-FP8.log",  "Qwen3.6-35B-A3B-FP8(MoE)",      "35B/3B",   "Qwen",       "Qwen/Qwen3.6-35B-A3B-FP8"),
    ("/tmp/ikp_AEON-7-Qwen3-6-35B-A3B-heretic-NVFP4.log", "Qwen3.6-35B-heretic-NVFP4", "35B/3B", "AEON-7", "AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4"),
    ("/tmp/ikp_Qwen-Qwen3-6-27B.log",           "Qwen3.6-27B",                    "27B",      "Qwen",       "Qwen/Qwen3.6-27B"),
    ("/tmp/ikp_Qwen-Qwen3-6-27B-FP8.log",       "Qwen3.6-27B-FP8",               "27B",      "Qwen",       "Qwen/Qwen3.6-27B-FP8"),
    ("/tmp/ikp_nvidia-Qwen3-5-397B-A17B-NVFP4.log",       "Qwen3.5-397B-A17B-NVFP4(MoE)", "397B/17B", "NVIDIA", "nvidia/Qwen3.5-397B-A17B-NVFP4"),
    ("/tmp/ikp_deepseek-ai-DeepSeek-V4-Flash.log",        "DeepSeek-V4-Flash",     "?",        "DeepSeek",   "deepseek-ai/DeepSeek-V4-Flash"),
    ("/tmp/ikp_moonshotai-Kimi-VL-A3B-Instruct.log",      "Kimi-VL-A3B",           "~3B",      "Moonshot",   "moonshotai/Kimi-VL-A3B-Instruct"),
    # ── Batch 2: Qwen3 dense series ──
    ("/tmp/ikp_Qwen-Qwen3-8B.log",                        "Qwen3-8B",              "8B",       "Qwen",       "Qwen/Qwen3-8B"),
    ("/tmp/ikp_Qwen-Qwen3-14B.log",                       "Qwen3-14B",             "14B",      "Qwen",       "Qwen/Qwen3-14B"),
    ("/tmp/ikp_Qwen-Qwen3-32B.log",                       "Qwen3-32B",             "32B",      "Qwen",       "Qwen/Qwen3-32B"),
    ("/tmp/ikp_Qwen-Qwen3-32B-FP8.log",                   "Qwen3-32B-FP8",         "32B",      "Qwen",       "Qwen/Qwen3-32B-FP8"),
    ("/tmp/ikp_nvidia-Qwen3-32B-NVFP4.log",               "Qwen3-32B-NVFP4",       "32B",      "NVIDIA",     "nvidia/Qwen3-32B-NVFP4"),
    # ── Batch 2: Llama-3.3 ──
    ("/tmp/ikp_meta-llama-Llama-3-3-70B-Instruct.log",    "Llama-3.3-70B",         "70B",      "Meta",       "meta-llama/Llama-3.3-70B-Instruct"),
    ("/tmp/ikp_nvidia-Llama-3-3-70B-Instruct-FP8.log",    "Llama-3.3-70B-FP8",     "70B",      "NVIDIA",     "nvidia/Llama-3.3-70B-Instruct-FP8"),
    # ── Batch 2: Phi-4 reasoning ──
    ("/tmp/ikp_microsoft-Phi-4-reasoning.log",             "Phi-4-reasoning",       "14B",      "Microsoft",  "microsoft/Phi-4-reasoning"),
    ("/tmp/ikp_nvidia-Phi-4-reasoning-plus-FP8.log",       "Phi-4-reasoning+-FP8",  "14B",      "NVIDIA",     "nvidia/Phi-4-reasoning-plus-FP8"),
    # ── Batch 2: NVIDIA Nemotron-3 Super ──
    ("/tmp/ikp_nvidia-NVIDIA-Nemotron-3-Super-120B-A12B-FP8.log", "Nemotron-3-Super-120B-A12B-FP8", "120B/12B", "NVIDIA", "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8"),
    # ── Batch 2: InternLM3 + Gemma-3 ──
    ("/tmp/ikp_internlm-internlm3-8b-instruct.log",        "InternLM3-8B",          "8B",       "InternLM",   "internlm/internlm3-8b-instruct"),
    ("/tmp/ikp_google-gemma-3-27b-it.log",                 "Gemma-3-27B",           "27B",      "Google",     "google/gemma-3-27b-it"),
]

TIERS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]

def parse(path):
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return None
    if "Estimated size:" not in text:
        return None
    r = {}
    m = re.search(r"Accuracy:\s+([\d.]+)%\s+\(penalized\)\s+([\d.]+)%\s+\(raw\)", text)
    if m:
        r["penalized"] = float(m.group(1))
        r["raw"]       = float(m.group(2))
    m = re.search(r"Estimated size:\s+(\S+)", text)
    r["estimated"] = m.group(1) if m else "N/A"
    for line in text.splitlines():
        tm = re.match(r"\s*(T\d)\s+(\d+)%\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if tm:
            t, acc, cor, wrg, ref, tot = tm.groups()
            r[t] = int(acc)
    return r

out = Path(__file__).parent / "benchmark.csv"
fields = ["Model", "Vendor", "HF_ID", "Actual", "Estimated", "Penalized_Acc", "Raw_Acc"] + TIERS

with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for log, name, actual, vendor, hf_id in LOG_MAP:
        d = parse(log)
        if not d:
            continue
        row = {
            "Model":         name,
            "Vendor":        vendor,
            "HF_ID":         hf_id,
            "Actual":        actual,
            "Estimated":     d.get("estimated", "N/A"),
            "Penalized_Acc": d.get("penalized", 0),
            "Raw_Acc":       d.get("raw", 0),
        }
        for t in TIERS:
            row[t] = d.get(t, 0)
        w.writerow(row)

print(f"Written {out}")
