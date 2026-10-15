"""Baseline Validation 평가 — baseline_best.pt (baseline_v4, kimchi_v4) 를 Validation 132장에서 평가한다 (가이드 18.1).

이력: kimchi_v1 첫 Baseline 의 평가 결과는 reports/baseline_v1_metrics.csv · baseline_v1_class_metrics.csv.

    python scripts/07_evaluate_baseline.py

결과:
    reports/baseline_metrics.csv          대표 성능 한 줄 (산출물 2)
    reports/baseline_class_metrics.csv    Class 별 성능
    reports/figures/baseline_results.png              학습 곡선 (산출물 5)
    reports/figures/baseline_confusion_matrix.png     Confusion Matrix (산출물 5)
    runs/eval/baseline_val/               Ultralytics 평가 원본 (PR 곡선 등)

Frozen Test 는 사용하지 않는다.
"""
import csv
import os
import shutil
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src.evaluate_detector import evaluate_detector  # noqa: E402
from src.train_detector import rel  # noqa: E402

MODEL_VERSION = "baseline_v4"
WEIGHT = PROJECT_ROOT / "models" / "baseline" / "baseline_best.pt"
TRAIN_RUN = PROJECT_ROOT / "runs" / MODEL_VERSION
DATA_YAML = PROJECT_ROOT / "configs" / "dataset.yaml"
REPORTS = PROJECT_ROOT / "reports"
FIGURES = REPORTS / "figures"


def dataset_version():
    with (PROJECT_ROOT / "manifests" / "val.csv").open(encoding="utf-8-sig") as f:
        return next(csv.DictReader(f))["dataset_version"]


def main():
    # 학습할 때 쓴 조건을 그대로 읽어 같은 imgsz 로 평가한다
    args = yaml.safe_load((TRAIN_RUN / "args.yaml").read_text(encoding="utf-8"))

    print("=" * 65)
    print(f" [Subject 08] Baseline Validation ({MODEL_VERSION} · {rel(WEIGHT)})")
    print("=" * 65)
    res = evaluate_detector(WEIGHT, DATA_YAML, split="val", imgsz=args["imgsz"], batch=args["batch"],
                            project=PROJECT_ROOT / "runs" / "eval", name=f"{MODEL_VERSION}_val")

    REPORTS.mkdir(exist_ok=True)
    metrics_csv = REPORTS / "baseline_metrics.csv"
    with metrics_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model_version", "dataset_version", "split", "imgsz", "batch", "epochs", "seed",
                    "images", "instances", "precision", "recall", "map50", "map50_95"])
        w.writerow([MODEL_VERSION, dataset_version(), "val", args["imgsz"], args["batch"], args["epochs"], args["seed"],
                    res["images"], res["instances"], res["precision"], res["recall"], res["map50"], res["map50_95"]])

    class_csv = REPORTS / "baseline_class_metrics.csv"
    with class_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res["per_class"][0]))
        w.writeheader()
        w.writerows(res["per_class"])

    # 그래프: 학습 곡선은 학습 실행 폴더, Confusion Matrix 는 이번 평가 폴더에서 (사진이 없는 그래프만)
    FIGURES.mkdir(parents=True, exist_ok=True)
    copies = {TRAIN_RUN / "results.png": FIGURES / "baseline_results.png",
              res["save_dir"] / "confusion_matrix.png": FIGURES / "baseline_confusion_matrix.png",
              res["save_dir"] / "confusion_matrix_normalized.png": FIGURES / "baseline_confusion_matrix_normalized.png",
              res["save_dir"] / "BoxPR_curve.png": FIGURES / "baseline_pr_curve.png"}
    for src, dst in copies.items():
        if src.is_file():
            shutil.copy2(src, dst)

    print(f"\n Validation {res['images']}장 · 정답 BBox {res['instances']}개")
    print(f" Precision {res['precision']:.3f} | Recall {res['recall']:.3f} | "
          f"mAP50 {res['map50']:.3f} | mAP50-95 {res['map50_95']:.3f}")
    print("\n Class 별")
    print(f" {'Class':<24}{'사진':>5}{'BBox':>6}{'P':>8}{'R':>8}{'mAP50':>8}{'mAP50-95':>10}")
    for r in res["per_class"]:
        if r["note"]:
            print(f" {r['class_id']} {r['class_name']:<22}{r['images']:>5}{r['instances']:>6}   {r['note']}")
        else:
            print(f" {r['class_id']} {r['class_name']:<22}{r['images']:>5}{r['instances']:>6}"
                  f"{r['precision']:>8.3f}{r['recall']:>8.3f}{r['map50']:>8.3f}{r['map50_95']:>10.3f}")
    print(f"\n 속도(ms/장): {res['speed_ms']}")
    print("\n 저장:")
    for p in (metrics_csv, class_csv, *[d for d in copies.values() if d.is_file()]):
        print(f"  -> {rel(p)}")
    print("=" * 65)


if __name__ == "__main__":
    main()
