#!/usr/bin/env python3
"""
Parse TrajLNS memory logs and plot metrics over time (sections).

Usage:
  python plot_mem_usage.py --log path/to/log.txt --out mem_usage.png --show
"""
import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Regex matches floats with optional exponent, optional +/-, and extra spaces
LINE_RE = re.compile(
    r'^\s*TrajLNS:(?P<key>[\w]+)_mem_GB\s*=\s*'
    r'(?P<val>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$'
)

START_KEYS = {"heuristics"}  # keys that mark potential start of a new section


def parse_sections(log_path: Path) -> pd.DataFrame:
    sections = []
    current = {}
    seen_start_key = False

    with log_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            m = LINE_RE.match(raw)
            if not m:
                continue
            key = m.group("key")
            val = float(m.group("val"))

            norm_key = key
            if norm_key in START_KEYS and seen_start_key and current:
                sections.append(current)
                current = {}
                seen_start_key = False

            if norm_key in START_KEYS:
                seen_start_key = True

            current[norm_key] = val

            if norm_key == "total":
                sections.append(current)
                current = {}
                seen_start_key = False

    if current:
        sections.append(current)

    if not sections:
        raise ValueError("No TrajLNS memory lines found in the log.")

    df = pd.DataFrame(sections)
    df.index.name = "section_index"
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def plot_df(df: pd.DataFrame, out_path: Path | None, show: bool):
    cols = sorted([c for c in df.columns if c != "total"]) + (["total"] if "total" in df.columns else [])
    df = df[cols]

    ax = df.plot()
    ax.set_xlabel("# Planner returns")
    ax.set_ylabel("Memory (GB)")
    ax.set_title("TrajLNS Memory Usage Over Sections")
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        print(f"Saved plot to {out_path}")
    if show or not out_path:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot TrajLNS memory usage from logs.")
    parser.add_argument("--log", type=Path, required=True, help="Path to log.txt")
    parser.add_argument("--out", type=Path, default=None, help="Output image path (e.g., mem_usage.png)")
    parser.add_argument("--show", action="store_true", help="Display the plot window")
    args = parser.parse_args()

    df = parse_sections(args.log)
    print("Parsed sections:", len(df))
    print(df.fillna(0).round(6).to_string())
    plot_df(df, args.out, args.show)


if __name__ == "__main__":
    main()
