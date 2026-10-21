"""Create the README portfolio chart from recorded CSVs; never runs a model.

Run from subject8/: python scripts/plot_portfolio.py
Outputs: reports/figures/comparison/portfolio_summary.svg and .png
"""
from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.constants import DEFAULT_DATASET_VERSION  # noqa: E402
from src.registry import OFFICIAL  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_metrics(root: Path = PROJECT_ROOT):
    """Read selected runs and the existing final test; reject mixed versions/models."""
    selected = [OFFICIAL["baseline"], "exp001_v5_imgsz1280",
                "exp002_v5_imgsz1920", OFFICIAL["final"]]
    rows = read_csv(root / "reports/runs_summary.csv")
    runs = []
    for name in selected:
        matches = [row for row in rows if row["run"] == name]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one summary row for {name}")
        row = matches[0]
        if row["dataset_version"] != DEFAULT_DATASET_VERSION:
            raise ValueError(f"Mixed Dataset Version: {name}")
        runs.append(row)
    tests = read_csv(root / "reports/05_final/final_metrics.csv")
    if len(tests) != 1:
        raise ValueError("Expected one recorded final test row")
    test = tests[0]
    if (test["model_version"] != OFFICIAL["final"]
            or test["dataset_version"] != DEFAULT_DATASET_VERSION
            or test["split"] != "test"):
        raise ValueError("Final test does not match the official model/version/split")
    return runs, test


def main():
    runs, test = load_metrics()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "group3-portfolio"})
    fig = plt.figure(figsize=(12.8, 5.1), facecolor="#f8fafc")
    ax = fig.add_axes([0.085, 0.25, 0.56, 0.50], facecolor="#f8fafc")
    values = [float(row["map50_95"]) for row in runs]
    colors = ["#94a3b8", "#60a5fa", "#3b82f6", "#0f766e"]
    ax.bar(range(4), values, width=0.55, color=colors, zorder=3)
    for x, value in enumerate(values):
        ax.text(x, value + 0.024, str(Decimal(runs[x]["map50_95"]).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)), ha="center", va="bottom",
                fontsize=15, fontweight="bold", color="#0f172a")
    labels = [f"{label}\n{row['model'].removesuffix('.pt')} / {row['imgsz']}"
              for label, row in zip(["Baseline", "exp001", "exp002", "Final"], runs)]
    ax.set_xticks(range(4), labels, fontsize=10)
    ax.set_ylim(0, 0.87)
    ax.set_ylabel("Validation mAP50-95", color="#475569")
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    ax.grid(axis="y", color="#e2e8f0", linewidth=1, zorder=0)
    ax.tick_params(axis="both", length=0, colors="#475569", pad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(0.065, 0.92, "FROM LABEL QUALITY TO OBJECT DETECTION",
             fontsize=11, color="#0f766e", fontweight="bold")
    fig.text(0.065, 0.845, "Validation improvement & final test",
             fontsize=18, color="#0f172a", fontweight="bold")
    fig.text(0.085, 0.765, f"{DEFAULT_DATASET_VERSION}  /  same validation split  /  best epoch",
             fontsize=10, color="#64748b")
    panel = fig.add_axes([0.71, 0.20, 0.26, 0.55], facecolor="#e8f3ef")
    panel.set_xticks([]); panel.set_yticks([])
    for spine in panel.spines.values():
        spine.set_visible(False)
    panel.text(0.10, 0.86, "FROZEN TEST", color="#0f766e", fontsize=11, fontweight="bold")
    panel.text(0.10, 0.57, f"{float(test['map50_95']):.3f}", color="#134e4a",
               fontsize=49, fontweight="bold")
    panel.text(0.10, 0.41, "mAP50-95", color="#134e4a", fontsize=13)
    panel.text(0.10, 0.23, f"Final model / {test['images']} images", color="#475569", fontsize=11)
    panel.text(0.10, 0.11, "Separate from model-selection Val", color="#475569", fontsize=9)
    fig.text(0.085, 0.115, "Final Val: selected best seed; see seed means and test-access history in the report.",
             fontsize=10, color="#64748b")
    fig.text(0.085, 0.065, "Limits: browning Test recall = 0; no negative (normal-only) images.",
             fontsize=10, color="#64748b")
    output = PROJECT_ROOT / "reports/figures/comparison"
    output.mkdir(parents=True, exist_ok=True)
    svg = output / "portfolio_summary.svg"
    fig.savefig(svg, metadata={"Date": None, "Title": "Group 3 portfolio: selected validation runs and final test",
                              "Description": "Recorded kimchi_v5 CSV results. Validation and Frozen Test are separate evaluations."})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    fig.savefig(output / "portfolio_summary.png", dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {svg.relative_to(PROJECT_ROOT)} and .png (recorded CSVs only)")


if __name__ == "__main__":
    main()
