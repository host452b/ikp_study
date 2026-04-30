#!/usr/bin/env python3
"""Export all IKP log results to benchmark.csv (utf-8-sig)."""
import re, csv
from pathlib import Path

LOG_MAP = {
    "/tmp/ikp_full.log":                        "Qwen2.5-VL-7B-FP8",
    "/tmp/ikp_thinking.log":                    "Qwen2.5-VL-7B-FP8+think",
    "/tmp/ikp_bf16.log":                        "Qwen2.5-VL-7B-BF16",
    "/tmp/ikp_nvfp4.log":                       "Qwen2.5-VL-7B-NVFP4",
    "/tmp/ikp_14b.log":                         "Qwen2.5-14B-BF16",
    "/tmp/ikp_Qwen-Qwen3-6-35B-A3B.log":       "Qwen3.6-35B-A3B(MoE)",
    "/tmp/ikp_Qwen-Qwen3-6-35B-A3B-FP8.log":  "Qwen3.6-35B-A3B-FP8(MoE)",
    "/tmp/ikp_Qwen-Qwen3-6-27B.log":           "Qwen3.6-27B",
    "/tmp/ikp_Qwen-Qwen3-6-27B-FP8.log":       "Qwen3.6-27B-FP8",
    "/tmp/ikp_deepseek-ai-DeepSeek-V4-Flash.log":        "DeepSeek-V4-Flash",
    "/tmp/ikp_moonshotai-Kimi-VL-A3B-Instruct.log":      "Kimi-VL-A3B",
    "/tmp/ikp_nvidia-Qwen3-5-397B-A17B-NVFP4.log":       "Qwen3.5-397B-A17B-NVFP4(MoE)",
    "/tmp/ikp_AEON-7-Qwen3-6-35B-A3B-heretic-NVFP4.log": "Qwen3.6-35B-heretic-NVFP4",
}

ACTUAL = {
    "Qwen2.5-VL-7B-FP8":               "7B",
    "Qwen2.5-VL-7B-FP8+think":         "7B",
    "Qwen2.5-VL-7B-BF16":              "7B",
    "Qwen2.5-VL-7B-NVFP4":             "7B",
    "Qwen2.5-14B-BF16":                "14B",
    "Qwen3.6-35B-A3B(MoE)":            "35B/3B",
    "Qwen3.6-35B-A3B-FP8(MoE)":        "35B/3B",
    "Qwen3.6-27B":                      "27B",
    "Qwen3.6-27B-FP8":                  "27B",
    "DeepSeek-V4-Flash":                "?",
    "Kimi-VL-A3B":                      "~3B",
    "Qwen3.5-397B-A17B-NVFP4(MoE)":   "397B/17B",
    "Qwen3.6-35B-heretic-NVFP4":        "35B/3B",
}

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
fields = ["Model", "Actual", "Estimated", "Penalized_Acc", "Raw_Acc"] + TIERS

with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for log, name in LOG_MAP.items():
        d = parse(log)
        if not d:
            continue
        row = {
            "Model":        name,
            "Actual":       ACTUAL.get(name, "?"),
            "Estimated":    d.get("estimated", "N/A"),
            "Penalized_Acc": d.get("penalized", 0),
            "Raw_Acc":      d.get("raw", 0),
        }
        for t in TIERS:
            row[t] = d.get(t, 0)
        w.writerow(row)

print(f"Written {out}")
