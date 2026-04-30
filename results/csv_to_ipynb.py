#!/usr/bin/env python3
"""
CSV → Jupyter Notebook with color-scaled HTML tables.

Flow:
  1. Read CSV (utf-8-sig)
  2. Split data into pages (PAGE_SIZE rows/page)
  3. Generate HTML tables with inline color styles
  4. Append leaderboard page (sorted by Penalized_Acc desc)
  5. Append quantization comparison page (original vs FP8 vs NVFP4, with Δ)
  6. Pack each page as a code cell with pre-computed display_data output
  7. GitHub auto-renders without execution

Color scale (score columns, mapped 0-100% → 0-10):
  ratio = max(0, min(1, (score - 3) / 7))
  ratio < 0.5 → red→yellow   (r=220, g=60+r*2*180, b=60)
  ratio ≥ 0.5 → yellow→green (r=220-(r-0.5)*2*180, g=200, b=60+(r-0.5)*2*40)
"""

import csv, json
from pathlib import Path

PAGE_SIZE = 50

SCORE_COLS = {"Penalized_Acc", "Raw_Acc", "T1", "T2", "T3", "T4", "T5", "T6", "T7"}
TIERS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]

# Model family → {quant_label: model_name_in_csv}
# "base" key marks which variant is the reference for Δ calculation
FAMILIES = {
    "Qwen2.5-VL-7B": {
        "base":     "Qwen2.5-VL-7B-BF16",
        "variants": {
            "BF16 (base)": "Qwen2.5-VL-7B-BF16",
            "FP8":         "Qwen2.5-VL-7B-FP8",
            "NVFP4":       "Qwen2.5-VL-7B-NVFP4",
            "FP8+think":   "Qwen2.5-VL-7B-FP8+think",
        },
    },
    "Qwen3.6-35B-A3B (MoE)": {
        "base":     "Qwen3.6-35B-A3B(MoE)",
        "variants": {
            "BF16 (base)":    "Qwen3.6-35B-A3B(MoE)",
            "FP8":            "Qwen3.6-35B-A3B-FP8(MoE)",
            "heretic-NVFP4":  "Qwen3.6-35B-heretic-NVFP4",
        },
    },
    "Qwen3.6-27B": {
        "base":     "Qwen3.6-27B",
        "variants": {
            "BF16 (base)": "Qwen3.6-27B",
            "FP8":         "Qwen3.6-27B-FP8",
        },
    },
    "Qwen2.5-14B": {
        "base":     "Qwen2.5-14B-BF16",
        "variants": {
            "BF16 (base)": "Qwen2.5-14B-BF16",
        },
    },
    "Qwen3.5-397B-A17B (MoE)": {
        "base":     "Qwen3.5-397B-A17B-NVFP4(MoE)",
        "variants": {
            "NVFP4": "Qwen3.5-397B-A17B-NVFP4(MoE)",
        },
    },
    "DeepSeek-V4-Flash": {
        "base":     "DeepSeek-V4-Flash",
        "variants": {"base": "DeepSeek-V4-Flash"},
    },
    "Kimi-VL-A3B": {
        "base":     "Kimi-VL-A3B",
        "variants": {"base": "Kimi-VL-A3B"},
    },
}

TABLE_CSS = (
    "<style>"
    "table{border-collapse:collapse;width:100%;font-size:13px}"
    "th{background:#2c3e50;color:#fff;padding:6px 10px;text-align:center;white-space:nowrap}"
    "td{padding:4px 8px;border:1px solid #ddd;text-align:center}"
    "td.left{text-align:left}"
    "tr:nth-child(even){background:#f8f8f8}"
    ".rank{font-weight:bold;color:#555}"
    ".delta-pos{color:#27ae60;font-weight:bold}"
    ".delta-neg{color:#e74c3c;font-weight:bold}"
    ".delta-neu{color:#888}"
    ".family-header td{background:#34495e;color:#fff;font-weight:bold;text-align:left;padding:6px 10px}"
    "</style>"
)


# ── Color helpers ──────────────────────────────────────────────

def score_color(pct: float) -> str:
    score = max(0.0, min(10.0, pct / 10.0))
    ratio = max(0.0, min(1.0, (score - 3) / 7))
    if ratio < 0.5:
        r, g, b = 220, int(60 + ratio * 2 * 180), 60
    else:
        r = int(220 - (ratio - 0.5) * 2 * 180)
        g = 200
        b = int(60 + (ratio - 0.5) * 2 * 40)
    return f"rgba({r},{g},{b},0.35)"


def td_score(val: str) -> str:
    try:
        bg = score_color(float(val))
        return f'<td style="background:{bg}">{val}</td>'
    except ValueError:
        return f"<td>{val}</td>"


def td_delta(delta: float) -> str:
    if abs(delta) < 0.05:
        return f'<td class="delta-neu">±0</td>'
    cls = "delta-pos" if delta > 0 else "delta-neg"
    sign = "+" if delta > 0 else ""
    return f'<td class="{cls}">{sign}{delta:.1f}</td>'


# ── Table builders ─────────────────────────────────────────────

def data_table_html(headers: list, rows: list, page: int, total: int) -> str:
    lines = [TABLE_CSS]
    if total > 1:
        lines.append(f"<p style='font-size:12px;color:#666'>Page {page}/{total}</p>")
    lines.append("<table><thead><tr>")
    for h in headers:
        lines.append(f"<th>{h}</th>")
    lines.append("</tr></thead><tbody>")
    for row in rows:
        lines.append("<tr>")
        for h in headers:
            v = row.get(h, "")
            if h in SCORE_COLS:
                lines.append(td_score(v))
            else:
                lines.append(f'<td class="left">{v}</td>')
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def leaderboard_html(all_rows: list) -> str:
    scored = []
    for row in all_rows:
        try:
            scored.append((float(row["Penalized_Acc"]), row))
        except (ValueError, KeyError):
            pass
    scored.sort(key=lambda x: x[0], reverse=True)

    lines = [TABLE_CSS]
    lines.append("<h3 style='font-family:sans-serif'>🏆 IKP Leaderboard — ranked by Penalized Accuracy</h3>")
    lines.append("<table><thead><tr>")
    for h in ["Rank", "Model", "Actual", "Estimated", "Penalized_Acc", "Raw_Acc"] + TIERS:
        lines.append(f"<th>{h}</th>")
    lines.append("</tr></thead><tbody>")
    for rank, (_, row) in enumerate(scored, 1):
        lines.append("<tr>")
        lines.append(f'<td class="rank">#{rank}</td>')
        lines.append(f'<td class="left"><b>{row["Model"]}</b></td>')
        lines.append(f'<td>{row.get("Actual","")}</td>')
        lines.append(f'<td>{row.get("Estimated","")}</td>')
        lines.append(td_score(row.get("Penalized_Acc", "0")))
        lines.append(td_score(row.get("Raw_Acc", "0")))
        for t in TIERS:
            lines.append(td_score(row.get(t, "0")))
        lines.append("</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def quant_comparison_html(all_rows: list) -> str:
    by_name = {r["Model"]: r for r in all_rows}
    metric_cols = ["Penalized_Acc", "Raw_Acc"] + TIERS

    lines = [TABLE_CSS]
    lines.append("<h3 style='font-family:sans-serif'>📊 Quantization Comparison — original vs quantized</h3>")
    lines.append("<p style='font-size:12px;color:#555;font-family:sans-serif'>"
                 "Δ columns show difference from BF16 base. "
                 "<span class='delta-pos'>green = improvement</span> · "
                 "<span class='delta-neg'>red = degradation</span></p>")

    for family, cfg in FAMILIES.items():
        variants = {k: v for k, v in cfg["variants"].items() if v in by_name}
        if not variants:
            continue
        base_name = cfg["base"]
        base_row = by_name.get(base_name, {})

        # Family header row
        n_cols = 2 + len(metric_cols) * 2  # quant + estimated + metrics + deltas
        lines.append("<table>")
        lines.append(f'<tr class="family-header"><td colspan="{n_cols + 2}">'
                     f'▶ {family}</td></tr>')

        # Column headers
        lines.append("<thead><tr>")
        lines.append("<th>Variant</th><th>Estimated</th>")
        for m in metric_cols:
            lines.append(f"<th>{m}</th>")
        for m in metric_cols:
            lines.append(f"<th>Δ {m}</th>")
        lines.append("</tr></thead><tbody>")

        for label, model_name in variants.items():
            row = by_name.get(model_name)
            if not row:
                continue
            is_base = (model_name == base_name)
            lines.append("<tr>")
            style = " style='font-weight:bold'" if is_base else ""
            lines.append(f'<td class="left"{style}>{label}</td>')
            lines.append(f'<td>{row.get("Estimated","")}</td>')
            for m in metric_cols:
                lines.append(td_score(row.get(m, "0")))
            for m in metric_cols:
                if is_base:
                    lines.append('<td class="delta-neu">—</td>')
                else:
                    try:
                        d = float(row.get(m, 0)) - float(base_row.get(m, 0))
                        lines.append(td_delta(d))
                    except ValueError:
                        lines.append("<td>—</td>")
            lines.append("</tr>")

        lines.append("</tbody></table><br>")

    return "\n".join(lines)


# ── Notebook builder ───────────────────────────────────────────

def html_cell(cell_id: str, source: str, html: str, exec_count: int) -> dict:
    return {
        "cell_type": "code",
        "id": cell_id,
        "execution_count": exec_count,
        "metadata": {},
        "source": source,
        "outputs": [{
            "output_type": "display_data",
            "metadata": {},
            "data": {"text/html": html, "text/plain": f"<{cell_id}>"},
        }],
    }


def md_cell(cell_id: str, source: str) -> dict:
    return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source}


def make_notebook(csv_path: Path, out_path: Path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        all_rows = list(reader)

    pages = [all_rows[i:i + PAGE_SIZE]
             for i in range(0, max(len(all_rows), 1), PAGE_SIZE)]
    total = len(pages)
    n = 0
    cells = []

    # ── Title ──
    cells.append(md_cell("title", (
        "# IKP Benchmark — All Models\n\n"
        f"Source: `{csv_path.name}` · **{len(all_rows)} models** · "
        f"{total} data page(s) · updated automatically after each run\n\n"
        "**Color scale** (Penalized_Acc, Raw_Acc, T1–T7): 🔴 low → 🟡 mid → 🟢 high\n\n"
        "---\n"
        "**Pages**\n"
        "1. Raw data table\n"
        "2. 🏆 Leaderboard (sorted by penalized accuracy)\n"
        "3. 📊 Quantization comparison (original vs FP8 vs NVFP4 + Δ)"
    )))

    # ── Data pages ──
    cells.append(md_cell("sec-data", "## Raw Data"))
    for i, page_rows in enumerate(pages, 1):
        n += 1
        cells.append(html_cell(
            f"data-p{i}",
            f"# Data page {i}/{total}",
            data_table_html(headers, page_rows, i, total),
            n,
        ))

    # ── Leaderboard ──
    n += 1
    cells.append(md_cell("sec-lb", "## 🏆 Leaderboard"))
    cells.append(html_cell("leaderboard", "# Leaderboard",
                            leaderboard_html(all_rows), n))

    # ── Quantization comparison ──
    n += 1
    cells.append(md_cell("sec-quant", "## 📊 Quantization Comparison"))
    cells.append(html_cell("quant-cmp", "# Quantization comparison",
                            quant_comparison_html(all_rows), n))

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12.0"},
        },
        "cells": cells,
    }
    out_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"Written {out_path}  ({len(all_rows)} models, {total} data page(s))")


if __name__ == "__main__":
    here = Path(__file__).parent
    make_notebook(here / "benchmark.csv", here / "benchmark.ipynb")
