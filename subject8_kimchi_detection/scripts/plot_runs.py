"""모든 학습 실행(runs/*/results.csv)의 그래프와 비교표를 다시 만든다 — 사진·모델 없이 Git 에 있는 기록만으로 동작.

    python scripts/plot_runs.py                              # 전체
    python scripts/plot_runs.py --runs baseline_v4 exp001_v4_imgsz1280 exp003_v4_imgsz1920_epoch100

결과 (Git 에 올림):
    reports/figures/runs/<실행>.png                       실행별 학습 곡선 (Loss 3종 · P/R · mAP50 · mAP50-95, best epoch 표시)
    reports/figures/runs_comparison_<Dataset Version>.png  같은 Version 실행끼리 Val mAP50-95 비교 (Val 이 같아야 비교가 공정)
    reports/runs_summary.csv                               실행별 Dataset Version · 조건(args.yaml) · best epoch 지표

Dataset Version 은 실행 이름의 `_v<N>` 으로 정한다 (예: exp001_v4_imgsz1280 → kimchi_v4). smoke_* 는 비교에서 뺀다.
새 실행도 이름에 `_v<N>` 을 넣는다.

Ultralytics 원본 그래프(실행당 약 1.8MB)는 Git 에 올리지 않고, 이 그림(실행당 약 0.1MB)으로 대신한다.
핵심 모델의 Confusion Matrix·PR 곡선은 07_evaluate_baseline.py 처럼 reports/figures/ 에 따로 둔다.
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS = PROJECT_ROOT / "runs"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "runs"
COMPARE_DIR = PROJECT_ROOT / "reports" / "figures"
SUMMARY_CSV = PROJECT_ROOT / "reports" / "runs_summary.csv"
SKIP = {"eval", "predict"}
PNG_META = {"Software": None}  # 다시 그려도 내용이 같으면 파일이 바뀌지 않게
VERSION_RE = re.compile(r"(?:^|_)v(\d+)(?:_|$)")


def dataset_version(run_name: str) -> str:
    """실행 이름 규칙으로 Dataset Version 을 정한다. smoke_* 는 Smoke 전용 작은 데이터"""
    if run_name.startswith("smoke"):
        return "smoke"
    m = VERSION_RE.search(run_name)
    return f"kimchi_v{m.group(1)}" if m else "unknown"


def read_results(run_dir: Path):
    with (run_dir / "results.csv").open(encoding="utf-8") as f:
        rows = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(f)]
    return [{k: float(v) for k, v in r.items() if v != ""} for r in rows]


def read_args(run_dir: Path) -> dict:
    p = run_dir / "args.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else {}


def best_row(rows):
    """Ultralytics 8.4 best.pt 기준과 같게 mAP50-95 최대 epoch"""
    return max(rows, key=lambda r: r["metrics/mAP50-95(B)"])


def plot_run(name: str, rows, args: dict, out: Path):
    ep = [r["epoch"] for r in rows]
    best = best_row(rows)
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.5))
    for ax, key in zip(axes[0], ("box_loss", "cls_loss", "dfl_loss")):
        ax.plot(ep, [r[f"train/{key}"] for r in rows], label="train", color="#2b6cb0")
        ax.plot(ep, [r[f"val/{key}"] for r in rows], label="val", color="#dd6b20")
        ax.set_title(key)
        ax.legend(fontsize=8)
    ax = axes[1][0]
    ax.plot(ep, [r["metrics/precision(B)"] for r in rows], label="Precision", color="#2f855a")
    ax.plot(ep, [r["metrics/recall(B)"] for r in rows], label="Recall", color="#c53030")
    ax.set_title("Val Precision / Recall")
    ax.legend(fontsize=8)
    for ax, key, title in ((axes[1][1], "metrics/mAP50(B)", "Val mAP50"), (axes[1][2], "metrics/mAP50-95(B)", "Val mAP50-95")):
        ax.plot(ep, [r[key] for r in rows], color="#6b46c1")
        ax.axvline(best["epoch"], color="gray", ls=":", lw=1)
        ax.scatter([best["epoch"]], [best[key]], color="#6b46c1", zorder=3)
        ax.annotate(f"{best[key]:.3f}", (best["epoch"], best[key]), textcoords="offset points", xytext=(4, -12), fontsize=8)
        ax.set_title(title)
    for ax in axes.flat:
        ax.set_xlabel("epoch", fontsize=8)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.3)
    cond = f"imgsz {args.get('imgsz', '?')} · epochs {args.get('epochs', '?')} · batch {args.get('batch', '?')} · " \
           f"{Path(str(args.get('model', '?'))).name} · {args.get('optimizer', '?')} lr0 {args.get('lr0', '?')}"
    fig.suptitle(f"{name} [{dataset_version(name)}]   ({cond})   best epoch {int(best['epoch'])}", fontsize=11)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=80, metadata=PNG_META)
    plt.close(fig)


def plot_comparison(version: str, data, out: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [3, 2]})
    for name, rows, _ in data:
        ax1.plot([r["epoch"] for r in rows], [r["metrics/mAP50-95(B)"] for r in rows], label=name, lw=1.2)
    ax1.set_title(f"{version} — Val mAP50-95 by epoch")
    ax1.set_xlabel("epoch")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=7, loc="lower right")
    names = [n for n, _, _ in data]
    vals = [best_row(rows)["metrics/mAP50-95(B)"] for _, rows, _ in data]
    bars = ax2.barh(names, vals, color="#6b46c1")
    ax2.bar_label(bars, fmt="%.3f", fontsize=8, padding=2)
    ax2.set_title("best Val mAP50-95")
    ax2.invert_yaxis()
    ax2.tick_params(labelsize=8)
    ax2.set_xlim(0, max(vals) * 1.15 if vals else 1)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=80, metadata=PNG_META)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="runs/*/results.csv 로 학습 그래프·비교표 만들기")
    ap.add_argument("--runs", nargs="*", help="실행 이름 (생략하면 results.csv 가 있는 전부)")
    args = ap.parse_args()

    names = args.runs or sorted(d.name for d in RUNS.iterdir()
                                if d.is_dir() and d.name not in SKIP and (d / "results.csv").is_file())
    data = []
    for name in names:
        run = RUNS / name
        if not (run / "results.csv").is_file():
            print(f" 건너뜀 (results.csv 없음): {name}")
            continue
        rows = read_results(run)
        if not rows:
            continue
        data.append((name, rows, read_args(run)))

    if not data:
        sys.exit("그릴 실행이 없습니다.")

    summary = []
    by_version = defaultdict(list)
    for name, rows, a in data:
        plot_run(name, rows, a, FIG_DIR / f"{name}.png")
        b = best_row(rows)
        version = dataset_version(name)
        if version != "smoke":
            by_version[version].append((name, rows, a))
        summary.append({
            "run": name, "dataset_version": version,
            "model": Path(str(a.get("model", ""))).name, "imgsz": a.get("imgsz", ""),
            "epochs": a.get("epochs", ""), "batch": a.get("batch", ""), "optimizer": a.get("optimizer", ""),
            "lr0": a.get("lr0", ""), "seed": a.get("seed", ""), "epochs_done": int(rows[-1]["epoch"]),
            "best_epoch": int(b["epoch"]), "precision": round(b["metrics/precision(B)"], 4),
            "recall": round(b["metrics/recall(B)"], 4), "map50": round(b["metrics/mAP50(B)"], 4),
            "map50_95": round(b["metrics/mAP50-95(B)"], 4),
        })
        print(f" {name:<34} {version:<10} best ep {int(b['epoch']):>3}  mAP50 {b['metrics/mAP50(B)']:.3f}  mAP50-95 {b['metrics/mAP50-95(B)']:.3f}")

    compare_files = []
    for version, runs in sorted(by_version.items()):
        out = COMPARE_DIR / f"runs_comparison_{version}.png"
        plot_comparison(version, runs, out)
        compare_files.append(out.name)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)

    print(f"\n 저장: reports/figures/runs/ ({len(data)}장), {', '.join(compare_files)}, reports/runs_summary.csv")
    print(" 비교 그래프는 같은 Dataset Version(같은 Validation)끼리만 묶었다.")
    print(" (참고) 학습 중 Validation 지표이며, 공식 평가는 07_evaluate_baseline.py 등으로 따로 한다.")


if __name__ == "__main__":
    main()
