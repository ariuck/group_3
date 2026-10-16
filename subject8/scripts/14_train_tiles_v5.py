"""개선 실험 exp004_v5 — 타일링: 4K 원본을 2×2 조각(20% 겹침)으로 잘라 학습하고, 조각 예측을 합쳐 원본 Val 로 채점한다.

    python scripts/14_train_tiles_v5.py             # 조각 만들기(없으면) → 학습 → 원본 Val 채점
    python scripts/14_train_tiles_v5.py --eval-only # 채점만 (학습된 Weight 로)

바꾸는 변수 하나: 입력 = 원본 사진 → 조각 사진 (exp002_v5 와 imgsz 1920 · batch 6 · 50 epoch 등 나머지 같음)
가설: 1920 으로 줄이면 작은 이물(작은 갈변 한 변 20~30px → 10px 안팎)이 사라진다. 조각은 축소 2.5배 → 약 1.4배.

결과:
    data/yolo_v5_tiles/{images,labels}/{train,val}   조각 (Test · Bridge 는 만들지 않음, Git 제외)
    configs/dataset_v5_tiles.yaml
    runs/exp004_v5_tile2x2/, models/improved/exp004_v5_tile2x2.pt (src/registry.weight_path)
    reports/04_improvement/exp004_v5_tile2x2_training_condition.md
    reports/04_improvement/tiling_eval.csv        원본 Val 104장 채점: exp002_v5(원본) vs exp004_v5(조각 합침)
학습 중 Validation 은 조각 단위라 다른 실험과 비교하지 않는다. 비교는 tiling_eval.csv (같은 채점 코드 src/tiling.evaluate_full).
"""
import argparse
import csv
import importlib.util
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from ultralytics import YOLO  # noqa: E402

from src import registry  # noqa: E402
from src.constants import CLASS_NAMES  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.tiling import evaluate_full, write_tiles  # noqa: E402
from src.train_detector import (  # noqa: E402
    best_epoch_metrics, check_training, copy_weight, rel, sha256_short, train_detector, write_condition_report,
)

_spec = importlib.util.spec_from_file_location("train_v5", PROJECT_ROOT / "scripts" / "11_train_v5.py")
v5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v5)

TILES = ((2, 2), 0.2)            # (grid, overlap)
SRC = SplitBuilder(PROJECT_ROOT, "kimchi_v5").yolo_dir
TILE_DIR = PROJECT_ROOT / "data" / "yolo_v5_tiles"
YAML = PROJECT_ROOT / "configs" / "dataset_v5_tiles.yaml"
RUN_NAME = "exp004_v5_tile2x2"
WEIGHT = registry.weight_path(RUN_NAME)
REPORT = PROJECT_ROOT / "reports" / "04_improvement" / f"{RUN_NAME}_training_condition.md"
EVAL_CSV = PROJECT_ROOT / "reports" / "04_improvement" / "tiling_eval.csv"
COMPARE_RUN = "exp002_v5_imgsz1920"     # 같은 조건(imgsz 1920)의 원본 입력 모델
CONDITION = dict(v5.tb.BASELINE, **v5.RUNS["exp002"]["change"])     # imgsz 1920 · batch 6 — exp002_v5 와 같음


def build_tiles():
    """train · val 원본 → 조각 (이미 사진 수 × 4 만큼 있으면 건너뜀)"""
    n_tiles = TILES[0][0] * TILES[0][1]
    for split in ("train", "val"):
        imgs = sorted((SRC / "images" / split).glob("*.jpg"))
        oi, ol = TILE_DIR / "images" / split, TILE_DIR / "labels" / split
        if oi.is_dir() and len(list(oi.glob("*.jpg"))) == len(imgs) * n_tiles:
            print(f" {split}: 조각 {len(imgs) * n_tiles}개 있음 → 건너뜀")
            continue
        oi.mkdir(parents=True, exist_ok=True)
        ol.mkdir(parents=True, exist_ok=True)
        for p in imgs:
            write_tiles(p, SRC / "labels" / split / f"{p.stem}.txt", oi, ol, *TILES)
        print(f" {split}: 원본 {len(imgs)}장 → 조각 {len(imgs) * n_tiles}개")
    names = "\n".join(f"  {k}: {v}" for k, v in CLASS_NAMES.items())
    YAML.write_text(f"# kimchi_v5 2×2 조각 (scripts/14_train_tiles_v5.py) — train·val 만\npath: data/yolo_v5_tiles\n"
                    f"train: images/train\nval: images/val\n\nnames:\n{names}\n", encoding="utf-8")


def train():
    if WEIGHT.exists():
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {WEIGHT}")
    print(" 조건: " + ", ".join(f"{k}={v}" for k, v in CONDITION.items()) + f", 입력 = 2×2 조각 (겹침 {TILES[1]:.0%})")
    result = train_detector(data_yaml=str(YAML), project=str(PROJECT_ROOT / "runs"), name=RUN_NAME, **CONDITION)
    checks = check_training(result)
    ok = all(passed for passed, _ in checks.values())
    if ok:
        copy_weight(result["best"], WEIGHT)
        checks["Weight 별도 보관"] = (WEIGHT.is_file(), f"`{rel(WEIGHT)}` (sha256 {sha256_short(WEIGHT)})")
    ref = best_epoch_metrics(result["results_csv"])
    notes = [
        "Frozen Test 와 Bridge Holdout 은 조각을 만들지 않았고 학습·검증에 쓰지 않았다.",
        "exp002_v5 (imgsz 1920 · batch 6) 와 다른 변수는 입력 하나: 원본 사진 → 2×2 조각(20% 겹침, 조각 2693×1502). "
        "조각 밖으로 40% 넘게 잘린 박스는 그 조각에서 뺐다.",
        "학습 중 Validation(아래 참고값)은 조각 단위라 다른 실험과 비교하지 않는다. 비교는 원본 Val 104장을 조각 예측 합침으로 채점한 "
        "`reports/04_improvement/tiling_eval.csv` (src/tiling.evaluate_full).",
    ]
    if ref:
        notes.append(f"참고 — 조각 Validation best epoch {ref['epoch']}: P {ref['precision']:.3f} · R {ref['recall']:.3f} · "
                     f"mAP50 {ref['map50']:.3f} · mAP50-95 {ref['map50_95']:.3f}")
    n = {s: len(list((TILE_DIR / "images" / s).glob("*.jpg"))) for s in ("train", "val")}
    write_condition_report(REPORT, f"kimchi_v5 개선 실험 exp004 학습 조건 (`{RUN_NAME}`)", {
        "Model": f"YOLO11n (`{CONDITION['model_name']}`, COCO 사전학습 · pretrained=True)",
        "Dataset Version": "`kimchi_v5` 2×2 조각",
        "Train / Val": f"조각 {n['train']}개 / {n['val']}개 (원본 558 / 104장 × 4)",
        "Data 설정": f"`{rel(YAML)}`",
        "Epoch": CONDITION["epochs"], "Batch": CONDITION["batch"], "Image Size": CONDITION["imgsz"],
        "Seed": f"{CONDITION['seed']} (deterministic=True)", "Optimizer": CONDITION["optimizer"],
        "Learning Rate (lr0)": CONDITION["lr0"], "Augmentation": "Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등)",
    }, result, checks, notes=notes)
    for k, (passed, detail) in checks.items():
        print(f" {'PASS' if passed else 'FAIL'}  {k}: {detail}")
    return ok


def evaluate():
    """원본 Val 104장, 같은 채점 코드: exp002_v5(원본 예측) vs exp004_v5(조각 예측 합침)"""
    pairs = [(p, SRC / "labels" / "val" / f"{p.stem}.txt") for p in sorted((SRC / "images" / "val").glob("*.jpg"))]
    rows = []
    for run, tiles in ((COMPARE_RUN, None), (RUN_NAME, TILES)):
        r = evaluate_full(YOLO(str(registry.find_weight(run))), pairs, CONDITION["imgsz"], tiles)
        print(f" {run}: P {r['precision']:.3f} R {r['recall']:.3f} mAP50 {r['map50']:.3f} mAP50-95 {r['map50_95']:.3f}")
        rows.append({"run": run, "input": "2x2 조각" if tiles else "원본", "class": "all", "instances": r["instances"],
                     **{k: round(r[k], 4) for k in ("precision", "recall", "map50", "map50_95")}})
        for c, m in sorted(r["per_class"].items()):
            rows.append({"run": run, "input": rows[-1]["input"], "class": c, "instances": m["instances"],
                         **{k: round(m[k], 4) for k in ("precision", "recall", "map50", "map50_95")}})
    with EVAL_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f" 저장: {rel(EVAL_CSV)}")


def main():
    ap = argparse.ArgumentParser(description="exp004_v5 타일링 학습·채점")
    ap.add_argument("--eval-only", action="store_true")
    args = ap.parse_args()
    if not args.eval_only:
        build_tiles()
        if not train():
            sys.exit(1)
    evaluate()


if __name__ == "__main__":
    main()
