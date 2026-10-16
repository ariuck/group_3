"""kimchi_v4 → kimchi_v5 에서 무엇이 좋아졌는지 한 장으로 (manifest · 라벨 · runs_summary 만으로, 사진·GPU 불필요).

    python scripts/plot_v5_vs_v4.py

결과: reports/figures/comparison/v5_vs_v4.png, reports/06_kimchi_v5/v5_vs_v4.csv
  ① 평가 사진 중 Train 과 같은 촬영 묶음 출신 (누수) ② 평가 역할의 Class 별 최소 박스 수
  ③ Val Class 별 박스 수 ④ 학습 중 best Val mAP50-95 (Val 이 달라 직접 비교 아님 — 그림에 표시)
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.split_builder import SplitBuilder  # noqa: E402

VERSIONS = {"kimchi_v4": PROJECT_ROOT / "manifests", "kimchi_v5": PROJECT_ROOT / "manifests" / "kimchi_v5"}
COLORS = {"kimchi_v4": "#2a78d6", "kimchi_v5": "#eb6834"}   # 범주색 1·2번 (dataviz 기본 팔레트)
TEXT, MUTED = "#0b0b0b", "#52514e"
EVAL = ["val", "test", "bridge_holdout"]
ROLE_KO = {"val": "Val", "test": "Test", "bridge_holdout": "Bridge"}
CLASSES = [0, 1, 2, 3, 5, 6]
CLASS_KO = {0: "c0 잎·종이", 1: "c1 플라스틱·돌", 2: "c2 가지", 3: "c3 벌레", 5: "c5 갈변", 6: "c6 파·고추"}
OUT_PNG = PROJECT_ROOT / "reports" / "figures" / "comparison" / "v5_vs_v4.png"
OUT_CSV = PROJECT_ROOT / "reports" / "06_kimchi_v5" / "v5_vs_v4.csv"
RUNS = {"kimchi_v4": ["baseline_v4", "exp001_v4_imgsz1280", "exp002_v4_imgsz1920"],
        "kimchi_v5": ["baseline_v5", "exp001_v5_imgsz1280", "exp002_v5_imgsz1920"]}


def stats(version, manifest_dir):
    b = SplitBuilder(PROJECT_ROOT, version)
    fix = b.label_fix_dir(version)
    rows = list(csv.DictReader((manifest_dir / "split_manifest.csv").open(encoding="utf-8-sig")))
    train_groups = {r["capture_group"] for r in rows if r["split"] == "train"}
    out = {"images": Counter(r["split"] for r in rows), "leak": Counter(), "boxes": {s: Counter() for s in ["train", *EVAL]}}
    for r in rows:
        if r["split"] in EVAL and r["capture_group"] in train_groups:
            out["leak"][r["split"]] += 1
        lbl = r["라벨(TXT) 파일명"]
        src = fix / lbl if (fix / lbl).is_file() else next(b.labels_dir.rglob(lbl))
        for line in src.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                out["boxes"][r["split"]][int(line.split()[0])] += 1
    out["split_groups"] = len({g for g in {r["capture_group"] for r in rows}
                               if len({x["split"] for x in rows if x["capture_group"] == g}) > 1})
    return out


def best_map():
    rows = {r["run"]: r for r in csv.DictReader((PROJECT_ROOT / "reports" / "04_improvement" / "runs_summary.csv").open(encoding="utf-8-sig"))}
    return {v: [float(rows[n]["map50_95"]) for n in names] for v, names in RUNS.items()}


def bars(ax, cats, values, labels_fmt="{:.0f}"):
    """버전 2개 묶음 막대 + 값 표시"""
    w = 0.38
    for k, v in enumerate(VERSIONS):
        xs = [i + (k - 0.5) * w for i in range(len(cats))]
        rect = ax.bar(xs, values[v], w - 0.03, color=COLORS[v], label=v)
        ax.bar_label(rect, [labels_fmt.format(x) for x in values[v]], fontsize=8, color=TEXT, padding=2)
    ax.set_xticks(range(len(cats)), cats, fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    plt.rcParams["font.family"] = [f for f in ("NanumGothic", "Noto Sans CJK KR", "Malgun Gothic") if f in
                                   {x.name for x in matplotlib.font_manager.fontManager.ttflist}][:1] or ["DejaVu Sans"]
    s = {v: stats(v, d) for v, d in VERSIONS.items()}
    m = best_map()
    fig, axs = plt.subplots(2, 2, figsize=(13, 8.5), facecolor="#fcfcfb")
    fig.suptitle("kimchi_v4 → kimchi_v5: 무엇이 달라졌나 (① 좋아짐 · ②③ 대가 · ④ 참고)", fontsize=14, color=TEXT)

    ax = axs[0, 0]
    bars(ax, [ROLE_KO[r] for r in EVAL],
         {v: [s[v]["leak"][r] / s[v]["images"][r] * 100 for r in EVAL] for v in VERSIONS}, "{:.0f}%")
    ax.set_title("① 평가 사진 중 Train 과 같은 촬영 묶음 출신 (낮을수록 좋음)", fontsize=10, color=TEXT)
    ax.set_ylabel("%", color=MUTED)
    for k, r in enumerate(EVAL):
        ax.annotate(" → ".join(f"{s[v]['leak'][r]}/{s[v]['images'][r]}" for v in VERSIONS), (k, -14),
                    ha="center", fontsize=8, color=MUTED, annotation_clip=False)
    ax.set_ylim(0, 75)
    ax.legend(frameon=False, fontsize=9)

    ax = axs[0, 1]
    bars(ax, [ROLE_KO[r] for r in EVAL],
         {v: [min(s[v]["boxes"][r][c] for c in CLASSES) for r in EVAL] for v in VERSIONS})
    ax.axhline(15, color=MUTED, linestyle="--", linewidth=1)
    ax.text(-0.45, 16, "기준 15", fontsize=8, color=MUTED, ha="left", va="bottom")
    ax.set_title("② 평가 역할의 가장 적은 Class 박스 수 (15 이상이어야 Recall 이 안정)", fontsize=10, color=TEXT)

    ax = axs[1, 0]
    bars(ax, [CLASS_KO[c] for c in CLASSES], {v: [s[v]["boxes"]["val"][c] for c in CLASSES] for v in VERSIONS})
    ax.set_title("③ Val Class 별 박스 수", fontsize=10, color=TEXT)
    ax.tick_params(axis="x", labelsize=8)

    ax = axs[1, 1]
    bars(ax, ["640", "1280", "1920"], m, "{:.3f}")
    ax.set_ylim(0, 0.9)
    ax.set_title("④ 학습 중 best Val mAP50-95 — Val 이 달라 직접 비교 아님", fontsize=10, color=TEXT)
    ax.set_xlabel("imgsz", color=MUTED)
    ax.text(1, 0.84, "v5 Val 은 Train 이 못 본 촬영 묶음 → 점수가 낮아도 실제에 더 가까운 값",
            ha="center", fontsize=8, color=MUTED)

    fig.text(0.5, 0.005, f"Train {s['kimchi_v4']['images']['train']} → {s['kimchi_v5']['images']['train']}장 · "
             f"나눠진 촬영 묶음 {s['kimchi_v4']['split_groups']} → {s['kimchi_v5']['split_groups']}개 · "
             "라벨: v5 는 이물 없는 박스 3개 삭제", ha="center", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "kimchi_v4", "kimchi_v5"])
        w.writerow(["train_images", s["kimchi_v4"]["images"]["train"], s["kimchi_v5"]["images"]["train"]])
        w.writerow(["split_groups", s["kimchi_v4"]["split_groups"], s["kimchi_v5"]["split_groups"]])
        for r in EVAL:
            w.writerow([f"{r}_images", s["kimchi_v4"]["images"][r], s["kimchi_v5"]["images"][r]])
            w.writerow([f"{r}_same_group_as_train", s["kimchi_v4"]["leak"][r], s["kimchi_v5"]["leak"][r]])
            for c in CLASSES:
                w.writerow([f"{r}_boxes_c{c}", s["kimchi_v4"]["boxes"][r][c], s["kimchi_v5"]["boxes"][r][c]])
        for k, size in enumerate(["640", "1280", "1920"]):
            w.writerow([f"best_val_map50_95_imgsz{size}", m["kimchi_v4"][k], m["kimchi_v5"][k]])
    print(f"저장: {OUT_PNG.relative_to(PROJECT_ROOT)}, {OUT_CSV.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
