#!/usr/bin/env python3
"""
CSV → Jupyter Notebook with color-scaled HTML tables.

Flow:
  1. Read CSV (utf-8-sig)
  2. Split into pages (PAGE_SIZE rows each)
  3. Generate HTML table with inline color styles
  4. Pack each page as a notebook code cell with display_data output
  5. GitHub auto-renders the pre-computed HTML outputs

Color scale (score columns, 0-10):
  Low  (≤5): rgba(220,  60,  60, 0.35)  red
  Mid  (6-7): rgba(220, 240,  60, 0.35)  yellow
  High (8-10): rgba( 40, 200, 100, 0.35)  green

  ratio = max(0, min(1, (score - 3) / 7))
  if ratio < 0.5:  r,g,b = 220, 60+ratio*2*180, 60
  else:            r,g,b = 220-(ratio-0.5)*2*180, 200, 60+(ratio-0.5)*2*40
"""

import csv, json, math
from pathlib import Path

PAGE_SIZE = 50

# Columns treated as 0-100% scores → map to 0-10 before coloring
SCORE_COLS = {"Penalized_Acc", "Raw_Acc", "T1", "T2", "T3", "T4", "T5", "T6", "T7"}


def score_color(value: float) -> str:
    """Return rgba(...) background string for a 0-10 score."""
    score = max(0.0, min(10.0, value))
    ratio = max(0.0, min(1.0, (score - 3) / 7))
    if ratio < 0.5:
        r = 220
        g = int(60 + ratio * 2 * 180)
        b = 60
    else:
        r = int(220 - (ratio - 0.5) * 2 * 180)
        g = 200
        b = int(60 + (ratio - 0.5) * 2 * 40)
    return f"rgba({r},{g},{b},0.35)"


def cell_style(col: str, raw_val: str) -> str:
    if col not in SCORE_COLS:
        return ""
    try:
        pct = float(raw_val)
    except ValueError:
        return ""
    score = pct / 10.0          # 0-100 % → 0-10 scale
    bg = score_color(score)
    return f" style=\"background:{bg}; text-align:center\""


TABLE_CSS = (
    "<style>"
    "table{border-collapse:collapse;width:100%;font-size:13px}"
    "th{background:#2c3e50;color:#fff;padding:6px 10px;text-align:center}"
    "td{padding:4px 8px;border:1px solid #ddd}"
    "tr:nth-child(even){background:#f9f9f9}"
    "</style>"
)


def rows_to_html(headers: list, rows: list, page: int, total_pages: int) -> str:
    lines = [TABLE_CSS]
    if total_pages > 1:
        lines.append(f"<p style='font-size:12px;color:#666'>Page {page}/{total_pages} "
                     f"({len(rows)} rows)</p>")
    lines.append("<table>")
    lines.append("<thead><tr>" +
                 "".join(f"<th>{h}</th>" for h in headers) +
                 "</tr></thead>")
    lines.append("<tbody>")
    for row in rows:
        cells = "".join(
            f"<td{cell_style(h, row.get(h,''))}"
            f"{'>' if cell_style(h,row.get(h,'')) else '>'}"
            f"{row.get(h,'')}</td>"
            for h in headers
        )
        lines.append(f"<tr>{cells}</tr>")
    lines.append("</tbody></table>")
    return "\n".join(lines)


def make_notebook(csv_path: Path, out_path: Path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        all_rows = list(reader)

    pages = [all_rows[i:i + PAGE_SIZE] for i in range(0, max(len(all_rows), 1), PAGE_SIZE)]
    total = len(pages)

    cells = []

    # Title cell
    cells.append({
        "cell_type": "markdown",
        "id": "title",
        "metadata": {},
        "source": (
            "# IKP Benchmark — All Models\n\n"
            f"Source: `{csv_path.name}` · {len(all_rows)} models · "
            f"{len(headers)} columns · {total} page(s) of {PAGE_SIZE}\n\n"
            "**Score columns** (Penalized_Acc, Raw_Acc, T1–T7): "
            "🔴 low · 🟡 medium · 🟢 high"
        ),
    })

    for i, page_rows in enumerate(pages, 1):
        html = rows_to_html(headers, page_rows, i, total)
        cells.append({
            "cell_type": "code",
            "id": f"page{i}",
            "execution_count": i,
            "metadata": {},
            "source": f"# Page {i}/{total}",
            "outputs": [{
                "output_type": "display_data",
                "metadata": {},
                "data": {"text/html": html, "text/plain": f"<Page {i}>"},
            }],
        })

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
    print(f"Written {out_path}  ({len(all_rows)} rows, {total} page(s))")


if __name__ == "__main__":
    here = Path(__file__).parent
    make_notebook(here / "benchmark.csv", here / "benchmark.ipynb")
