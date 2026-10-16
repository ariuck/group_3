"""kimchi_v5 (C안 재분할) 학습 — 06 Baseline 조건 + 10 의 해상도 실험(exp001·exp002)을 v5 에서 다시 한다.

    python scripts/03_build_split.py --version kimchi_v5 --copy-files   # 먼저 data/yolo_v5 만들기 (data/yolo 는 그대로)
    python scripts/11_train_v5.py                  # baseline → exp001 → exp002 차례로
    python scripts/11_train_v5.py --run exp001     # 하나만

  baseline : imgsz 640              → runs/baseline_v5/,           models/baseline/baseline_v5_best.pt
  exp001   : imgsz 1280             → runs/exp001_v5_imgsz1280/,   models/improved/exp001_v5_best.pt
  exp002   : imgsz 1920 · batch 6   → runs/exp002_v5_imgsz1920/,   models/improved/exp002_v5_best.pt
  조건 기록: reports/06_kimchi_v5/<실행>_training_condition.md

조건은 06(BASELINE)·10(EXPERIMENTS) 에서 그대로 가져온다. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.
분할 기준: docs/project/kimchi_v5_split.md
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)  # dataset_v5.yaml 의 path: data/yolo_v5 는 이 폴더 기준

from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import (  # noqa: E402
    best_epoch_metrics, check_training, copy_weight, rel, sha256_short, train_detector, write_condition_report,
)

# 10 을 불러오면 06(tb)도 함께 불러온다 — 조건은 두 곳에서만 관리
_spec = importlib.util.spec_from_file_location("train_v2", PROJECT_ROOT / "scripts" / "10_train_v2.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
tb = ex.tb

DATASET_VERSION = "kimchi_v5"
paths = SplitBuilder(PROJECT_ROOT, DATASET_VERSION)
# 06 의 precheck 가 v5 폴더를 보게 한다
tb.DATA_YAML, tb.MANIFEST_DIR, tb.YOLO_DIR = paths.dataset_yaml, paths.manifest_dir, paths.yolo_dir

RUNS = {
    "baseline": {"change": {}, "run_name": "baseline_v5", "weight": "baseline/baseline_v5_best.pt",
                 "title": "kimchi_v5 Baseline"},
    "exp001": {"change": ex.EXPERIMENTS["exp001"]["change"], "run_name": "exp001_v5_imgsz1280",
               "weight": "improved/exp001_v5_best.pt", "title": "kimchi_v5 개선 실험 exp001", "compare": "baseline_v5 (imgsz 640)"},
    "exp002": {"change": ex.EXPERIMENTS["exp002"]["change"], "run_name": "exp002_v5_imgsz1920",
               "weight": "improved/exp002_v5_best.pt", "title": "kimchi_v5 개선 실험 exp002", "compare": "exp001_v5 (imgsz 1280)",
               "note": ex.EXPERIMENTS["exp002"]["note"]},
}
REPORT_DIR = PROJECT_ROOT / "reports" / "06_kimchi_v5"


def train_one(key, counts):
    spec = RUNS[key]
    cond = dict(tb.BASELINE, **spec["change"])
    run_name = spec["run_name"]
    weight = PROJECT_ROOT / "models" / spec["weight"]
    report = REPORT_DIR / f"{run_name}_training_condition.md"
    if weight.exists():
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {weight} (덮어쓰지 않음)")
    print("=" * 65)
    print(f" [Subject 08] {run_name} (Dataset {DATASET_VERSION})")
    print("=" * 65)
    print(" 조건: " + ", ".join(f"{k}={v}" for k, v in cond.items()))

    result = train_detector(data_yaml=str(paths.dataset_yaml), project=str(PROJECT_ROOT / "runs"), name=run_name, **cond)
    checks = check_training(result)
    ok = all(passed for passed, _ in checks.values())
    if ok:
        copy_weight(result["best"], weight)
        checks["Weight 별도 보관"] = (weight.is_file(), f"`{rel(weight)}` (sha256 {sha256_short(weight)})")

    ref = best_epoch_metrics(result["results_csv"])
    notes = [
        f"Frozen Test 와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `{rel(paths.yolo_dir)}/train·val` 이 manifest 와 정확히 같은지 확인했다.",
        "kimchi_v5 = C안 재분할(묶음 통째 배정, 예외는 G00 하나) + 라벨 수정본 kimchi_v5(v3 + 이물 없는 박스 3개 삭제). "
        "기준: `docs/project/kimchi_v5_split.md`. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.",
    ]
    if spec["change"]:
        notes.append("Baseline(06) 조건에서 " + ", ".join(f"{k} {tb.BASELINE[k]} → {v}" for k, v in spec["change"].items())
                     + f" 으로 바꿨다. 비교 대상: {spec['compare']}.")
    if spec.get("note"):
        notes.append(spec["note"])
    if ref:
        notes.append(f"참고 — best.pt 가 저장된 epoch {ref['epoch']} 의 학습 중 Validation: "
                     f"P {ref['precision']:.3f} · R {ref['recall']:.3f} · mAP50 {ref['map50']:.3f} · mAP50-95 {ref['map50_95']:.3f}")
    manifest = rel(paths.manifest_dir)
    write_condition_report(
        report,
        f"{spec['title']} 학습 조건 (`{run_name}`)",
        {
            "Model": f"YOLO11n (`{cond['model_name']}`, COCO 사전학습 · pretrained=True)",
            "Dataset Version": f"`{DATASET_VERSION}`",
            "Train / Val Manifest": f"`{manifest}/train.csv` {counts['train']}장 (sha256 {sha256_short(paths.manifest_dir / 'train.csv')}) / "
                                    f"`{manifest}/val.csv` {counts['val']}장 (sha256 {sha256_short(paths.manifest_dir / 'val.csv')})",
            "Data 설정": f"`{rel(paths.dataset_yaml)}` (Class ID 0~6, Class 4 미사용)",
            "Epoch": cond["epochs"],
            "Batch": cond["batch"],
            "Image Size": cond["imgsz"],
            "Seed": f"{cond['seed']} (deterministic=True)",
            "Optimizer": cond["optimizer"],
            "Learning Rate (lr0)": cond["lr0"],
            "Augmentation": "Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등)",
        },
        result,
        checks,
        notes=notes,
    )
    for k, (passed, detail) in checks.items():
        print(f" {'PASS' if passed else 'FAIL'}  {k}: {detail}")
    if ref:
        print(f" (참고) best epoch {ref['epoch']}: mAP50 {ref['map50']:.3f} / mAP50-95 {ref['map50_95']:.3f}")
    print(f" 기록: {rel(report)} · 걸린 시간: {result['seconds'] // 60}분 {result['seconds'] % 60}초")
    return ok


def main():
    ap = argparse.ArgumentParser(description="kimchi_v5 학습 (baseline · exp001 · exp002)")
    ap.add_argument("--run", default="all", choices=["all", *RUNS])
    args = ap.parse_args()
    dataset_version, counts = tb.precheck()
    if dataset_version != DATASET_VERSION:
        raise RuntimeError(f"{rel(paths.yolo_dir)} 가 {dataset_version} 입니다.\n"
                           f"  python scripts/03_build_split.py --version {DATASET_VERSION} --copy-files")
    print(f" Dataset {dataset_version}: train {counts['train']}장 / val {counts['val']}장 (manifest 와 폴더 일치)")
    for key in (RUNS if args.run == "all" else [args.run]):
        if not train_one(key, counts):
            sys.exit(1)


if __name__ == "__main__":
    main()
