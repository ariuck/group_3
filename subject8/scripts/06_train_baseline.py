"""Baseline 학습 — 한 Dataset Version 의 Train 전체로 YOLO11n 을 학습한다 (가이드 17장).

    python scripts/06_train_baseline.py                       # 공식 Version (kimchi_v5) → baseline_v5
    python scripts/06_train_baseline.py --version kimchi_v4   # 지난 Version 재현 → baseline_v4

결과 (공식 Version):
    runs/baseline_v<N>/                                    Ultralytics 원본 결과 (results.csv, weights/best.pt …)
    models/baseline/baseline_v<N>.pt + baseline_best.pt    Weight 보관 (src/registry.py — 공식 Baseline 이면 가이드 이름 복사본도)
    reports/02_baseline/baseline_training_condition.md     학습 조건·환경·점검 기록 (산출물 2)
지난 Version: models/history/<Version>/baseline_v<N>.pt, reports/history/<Version>/baseline_v<N>_training_condition.md

Baseline 조건은 아래 BASELINE 한 곳에서만 정한다. 개선 실험은 이 값에서 변수 하나만 바꾼다 (exp001 = imgsz).
Validation 공식 평가(baseline_metrics.csv)는 07 에서 한다.
가이드 11.5·20.5 에 따라 Dataset Version 이 바뀌면 같은 Version 에서 Baseline 을 다시 학습한다 (v1 → v4 → v5).
"""
import argparse
import csv
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)  # dataset.yaml 의 path: data/yolo 는 이 폴더 기준

from src import registry  # noqa: E402
from src.constants import DATASET_VERSIONS, DEFAULT_DATASET_VERSION  # noqa: E402
from src.split_builder import SplitBuilder  # noqa: E402
from src.train_detector import (  # noqa: E402
    best_epoch_metrics, check_training, copy_weight, rel, sha256_short, train_detector, write_condition_report,
)

# ── Baseline 조건 (팀 확정값) ─────────────────────────────────────────────
BASELINE = {
    "model_name": "yolo11n.pt",   # COCO 사전학습 Weight 에서 시작 (pretrained)
    "epochs": 50,
    "imgsz": 640,                 # 4K 원본을 640 으로 줄여 학습. 작은 이물 FN 이 많으면 7일차에 960 비교
    "batch": 16,                  # Smoke Test 에서 GPU 2.1GB 사용 확인 (RTX 3060 12GB)
    "seed": 42,
    "optimizer": "AdamW",         # auto 대신 고정: 실험마다 Optimizer 가 자동으로 바뀌지 않게
    "lr0": 0.001,                 # AdamW 권장 초기 학습률
}
DATASET_VERSION = DEFAULT_DATASET_VERSION   # main() 의 --version 으로 바꿀 수 있다. 폴더가 이 Version 이 아니면 학습하지 않는다
_paths = SplitBuilder(PROJECT_ROOT, DATASET_VERSION)
# 아래 세 값은 10 · 11 이 precheck() 전에 자기 Version 폴더로 바꿔 쓴다
DATA_YAML = _paths.dataset_yaml
MANIFEST_DIR = _paths.manifest_dir
YOLO_DIR = _paths.yolo_dir


def read_manifest(split):
    with (MANIFEST_DIR / f"{split}.csv").open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def precheck():
    """학습 전에 확인 (가이드 4장 예시 1): yaml, 폴더 = manifest, Dataset Version"""
    if not DATA_YAML.is_file():
        raise FileNotFoundError(f"{DATA_YAML} 이 없습니다. python scripts/03_build_split.py")
    versions, counts = set(), {}
    for split in ("train", "val"):
        rows = read_manifest(split)
        want = {Path(r["이미지 파일명"]).stem for r in rows}
        have_img = {p.stem for p in (YOLO_DIR / "images" / split).iterdir()} if (YOLO_DIR / "images" / split).is_dir() else set()
        have_lbl = {p.stem for p in (YOLO_DIR / "labels" / split).glob("*.txt")}
        if want != have_img or want != have_lbl:
            raise RuntimeError(
                f"{rel(YOLO_DIR)}/{split} 가 {rel(MANIFEST_DIR)}/{split}.csv 와 다릅니다 "
                f"(manifest {len(want)} / 이미지 {len(have_img)} / 라벨 {len(have_lbl)}, "
                f"manifest 에 없는 파일 {len(have_img - want)}).\n"
                f"  python scripts/03_build_split.py --copy-files 로 다시 만드세요.")
        versions |= {r["dataset_version"] for r in rows}
        counts[split] = len(rows)
    if len(versions) != 1:
        raise RuntimeError(f"Dataset Version 이 하나가 아닙니다: {versions}")
    return versions.pop(), counts


def main():
    global DATA_YAML, MANIFEST_DIR, YOLO_DIR
    ap = argparse.ArgumentParser(description="Baseline 학습 (YOLO11n)")
    ap.add_argument("--version", default=DEFAULT_DATASET_VERSION, choices=DATASET_VERSIONS)
    args = ap.parse_args()
    version = args.version
    paths = SplitBuilder(PROJECT_ROOT, version)
    DATA_YAML, MANIFEST_DIR, YOLO_DIR = paths.dataset_yaml, paths.manifest_dir, paths.yolo_dir
    run_name = f"baseline_{version.replace('kimchi_', '')}"
    weight = registry.weight_path(run_name)
    official = version == DEFAULT_DATASET_VERSION
    report = (PROJECT_ROOT / "reports" / "02_baseline" / "baseline_training_condition.md" if official
              else PROJECT_ROOT / "reports" / "history" / version / f"{run_name}_training_condition.md")

    print("=" * 65)
    print(f" [Subject 08] Baseline Training (YOLO11n · {run_name})")
    print("=" * 65)
    if weight.exists():
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {weight} (덮어쓰지 않음)")
    dataset_version, counts = precheck()
    if dataset_version != version:
        raise RuntimeError(f"{rel(YOLO_DIR)} 가 {dataset_version} 입니다. Baseline 은 {version} 로 학습합니다.\n"
                           f"  python scripts/03_build_split.py --version {version} --copy-files")
    print(f" Dataset {dataset_version}: train {counts['train']}장 / val {counts['val']}장 (manifest 와 폴더 일치)")
    print(" 조건: " + ", ".join(f"{k}={v}" for k, v in BASELINE.items()))

    result = train_detector(data_yaml=str(DATA_YAML), project=str(PROJECT_ROOT / "runs"), name=run_name, **BASELINE)
    checks = check_training(result)
    ok = all(passed for passed, _ in checks.values())

    if ok:
        copy_weight(result["best"], weight)
        checks["Baseline Weight 별도 보관"] = (weight.is_file(), f"`{rel(weight)}` (sha256 {sha256_short(weight)})")
        if official and registry.OFFICIAL["baseline"] == run_name:
            shutil.copy2(weight, registry.ALIASES["baseline"])
            checks["공식 이름 복사본"] = (registry.ALIASES["baseline"].is_file(), f"`{rel(registry.ALIASES['baseline'])}`")

    ref = best_epoch_metrics(result["results_csv"])
    notes = [
        f"Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `{rel(YOLO_DIR)}/train·val` 이 manifest 와 정확히 같은지 확인했다.",
        f"이 Weight 는 {version} Train 전체로 학습한 기준 모델이다. 개선 실험은 같은 Version·같은 Val 에서 비교한다.",
        "이력: kimchi_v1 첫 Baseline 의 실패 분석으로 Dataset 을 v2~v4 로 고쳤고, v4 의 Val 누수를 없애려 v5 로 다시 나눴다. "
        "가이드 11.5·20.5 에 따라 Version 마다 같은 Version 에서 Baseline 을 다시 학습했다.",
        "Validation 공식 평가와 `reports/02_baseline/baseline_metrics.csv` 는 `scripts/07_evaluate_baseline.py` 로 작성한다.",
    ]
    if ref:
        notes.append(f"참고 — best.pt 가 저장된 epoch {ref['epoch']} 의 학습 중 Validation: "
                     f"P {ref['precision']:.3f} · R {ref['recall']:.3f} · mAP50 {ref['map50']:.3f} · mAP50-95 {ref['map50_95']:.3f}")

    manifest = rel(MANIFEST_DIR)
    write_condition_report(
        report,
        f"Baseline 학습 조건 (`{run_name}`)",
        {
            "Model": f"YOLO11n (`{BASELINE['model_name']}`, COCO 사전학습 · pretrained=True)",
            "Dataset Version": f"`{dataset_version}`",
            "Train / Val Manifest": f"`{manifest}/train.csv` {counts['train']}장 (sha256 {sha256_short(MANIFEST_DIR / 'train.csv')}) / "
                                    f"`{manifest}/val.csv` {counts['val']}장 (sha256 {sha256_short(MANIFEST_DIR / 'val.csv')})",
            "Data 설정": f"`{rel(DATA_YAML)}` (Class ID 0~6, Class 4 미사용)",
            "Epoch": BASELINE["epochs"],
            "Batch": BASELINE["batch"],
            "Image Size": BASELINE["imgsz"],
            "Seed": f"{BASELINE['seed']} (deterministic=True)",
            "Optimizer": BASELINE["optimizer"],
            "Learning Rate (lr0)": BASELINE["lr0"],
            "Augmentation": "Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등)",
        },
        result,
        checks,
        notes=notes,
    )

    print("\n-----------------------------------------------------------------")
    print(" [Baseline Checks]")
    print("-----------------------------------------------------------------")
    for k, (passed, detail) in checks.items():
        print(f" {'PASS' if passed else 'FAIL'}  {k}: {detail}")
    if ref:
        print(f"\n (참고) best epoch {ref['epoch']}: mAP50 {ref['map50']:.3f} / mAP50-95 {ref['map50_95']:.3f} — 공식 평가는 5일차")
    print(f" 기록: {rel(report)}")
    print("=" * 65)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
