"""Final Model Frozen Test 평가 — Final Model 을 Validation 근거로 확정한 뒤 **한 번만** 실행한다 (가이드 21장, 산출물 5).

    python scripts/16_evaluate_final_test.py

순서 (가이드 21.1): Validation 으로 Final 선택 → models/final/final_best.pt 복사 · src/registry.py OFFICIAL["final"] 에 실행 이름
→ reports/final_model_selection.md 작성 → 이 스크립트 (Frozen Test 82장).
결과는 보고만 한다 — 이 점수를 보고 모델·조건을 다시 고르지 않는다 (가이드 4037행).

결과:
    reports/05_final/final_metrics.csv · final_class_metrics.csv          Frozen Test 성능 (산출물 5)
    reports/figures/final/final_test_{confusion_matrix, confusion_matrix_normalized, pr_curve}.png
"""
import csv
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src import registry  # noqa: E402
from src.evaluate_detector import evaluate_detector  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import rel, sha256_short  # noqa: E402

OUT_DIR = PROJECT_ROOT / "reports" / "05_final"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "final"
SELECTION = PROJECT_ROOT / "reports" / "final_model_selection.md"


def main():
    weight, run = registry.resolve("final")            # Final 이 정해지지 않았으면 여기서 멈춘다
    if not SELECTION.is_file():
        sys.exit(f"{rel(SELECTION)} 가 없습니다. Final 선택 이유를 먼저 기록하세요 (가이드 21.1).")
    if any(OUT_DIR.glob("final_metrics.csv")):
        sys.exit(f"{rel(OUT_DIR / 'final_metrics.csv')} 가 이미 있습니다. Frozen Test 는 한 번만 평가합니다.")
    version = registry.run_version(run)
    a = registry.run_args(run)
    data = SplitBuilder(PROJECT_ROOT, version).dataset_yaml
    print("=" * 65)
    print(f" [Subject 08] Frozen Test — {run} ({rel(weight)}, sha256 {sha256_short(weight)}) · imgsz {a['imgsz']}")
    print("=" * 65)
    r = evaluate_detector(weight, data, "test", a["imgsz"], max(1, a["batch"]), project=PROJECT_ROOT / "runs" / "eval",
                          name=f"final_test_{run}", allow_test=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "final_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model_version", "dataset_version", "split", "imgsz", "batch", "epochs", "seed",
                    "images", "instances", "precision", "recall", "map50", "map50_95"])
        w.writerow([run, version, "test", a["imgsz"], a["batch"], a["epochs"], a["seed"],
                    r["images"], r["instances"], r["precision"], r["recall"], r["map50"], r["map50_95"]])
    with (OUT_DIR / "final_class_metrics.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(r["per_class"][0]))
        w.writeheader()
        w.writerows(r["per_class"])
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in (("confusion_matrix.png", "final_test_confusion_matrix.png"),
                     ("confusion_matrix_normalized.png", "final_test_confusion_matrix_normalized.png"),
                     ("BoxPR_curve.png", "final_test_pr_curve.png")):
        if (r["save_dir"] / src).is_file():
            shutil.copy2(r["save_dir"] / src, FIG_DIR / dst)
    print(f"\n Frozen Test {r['images']}장 · 정답 {r['instances']}개")
    print(f" P {r['precision']:.3f} | R {r['recall']:.3f} | mAP50 {r['map50']:.3f} | mAP50-95 {r['map50_95']:.3f}")
    for c in r["per_class"]:
        if c["instances"]:
            print(f"  {c['class_id']} {c['class_name']:<22} {c['instances']:>4}  mAP50-95 {c['map50_95']:.3f}")
    print(f" 저장: {rel(OUT_DIR)}/, {rel(FIG_DIR)}/")


if __name__ == "__main__":
    main()
