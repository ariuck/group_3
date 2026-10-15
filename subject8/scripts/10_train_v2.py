"""개선 실험 — 06 Baseline 조건에서 변수 하나씩 바꾼다 (가이드 20장 한 변수 실험).

    python scripts/10_train_v2.py               # exp001: imgsz 640 → 1280 (Baseline 대비)
    python scripts/10_train_v2.py --exp exp002  # exp002: imgsz 1280 → 1920 (exp001 대비, batch 6 — 아래)
    python scripts/10_train_v2.py --exp exp003  # exp003: epochs 50 → 100 (exp002 대비)

  kimchi_v4 (공식) : exp001 → runs/exp001_v4_imgsz1280/, models/improved/exp001_best.pt, reports/exp001_training_condition.md
                     exp002 → runs/exp002_v4_imgsz1920/, models/improved/exp002_best.pt, reports/exp002_training_condition.md
                     exp003 → runs/exp003_v4_imgsz1920_epoch100/, models/improved/exp003_best.pt, reports/exp003_training_condition.md
                     Baseline 은 06 의 baseline_v4 (같은 Version·같은 Val)
  kimchi_v1~v3 (이력, exp001 만): pilot_v1_imgsz1280 (예비 실험), history_v2/v3_imgsz1280 (데이터 개선 과정)

근거 (6일차 H4): 원본 4848×2704 를 640 으로 줄이면 박스 한 변 중앙값이 18~40px 이고,
leaf_paper·plastic·disease_browning 은 15~19% 가 16px 미만이 된다. 예비 실험(kimchi_v1)에서 mAP50-95 0.351 → 0.519.
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)  # dataset.yaml 의 path: data/yolo 는 이 폴더 기준

from src.train_detector import (  # noqa: E402
    best_epoch_metrics, check_training, copy_weight, rel, sha256_short, train_detector, write_condition_report,
)

# 06 의 BASELINE·precheck 를 그대로 쓴다 (조건은 06 한 곳에서만 관리)
_spec = importlib.util.spec_from_file_location("train_baseline", PROJECT_ROOT / "scripts" / "06_train_baseline.py")
tb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tb)

# ── 06 BASELINE 에서 바꾸는 값 (실험별). 비교 대상과 다른 변수는 imgsz 하나 ──
EXPERIMENTS = {
    # batch 16 그대로 — RTX 3060 에서 GPU 약 9.2GB 확인
    "exp001": {"change": {"imgsz": 1280}, "compare": "baseline_v4 (imgsz 640)"},
    # 1920 은 batch 8 에서도 12.9GB 로 12GB 를 넘어 공유 메모리로 넘치며 2.2s/it 로 느려졌다 → batch 6.
    # Ultralytics 는 nbs=64 에 맞춰 gradient 를 누적하므로 (batch 16 → 4번, 6 → 11번 모아 1번 갱신)
    # 갱신 1번에 들어가는 사진 수는 64장 · 66장으로 거의 같다
    "exp002": {"change": {"imgsz": 1920, "batch": 6}, "compare": "exp001 (imgsz 1280)",
               "note": "batch 16 → 6 은 GPU 메모리 때문이다 (batch 8 은 12.9GB 로 12GB 초과). "
                       "nbs=64 gradient 누적으로 갱신 1번당 사진 수는 exp001 64장 · exp002 66장으로 거의 같다."},
    # exp002 는 best epoch 이 마지막(50)이고 Val cls_loss 가 48 epoch 까지 내려가는 중이었다 → 학습량(epochs)만 늘린다
    "exp003": {"change": {"imgsz": 1920, "batch": 6, "epochs": 100}, "compare": "exp002 (epochs 50)",
               "run_name": "exp003_v4_imgsz1920_epoch100",
               "note": "exp002 와 다른 변수는 epochs(50 → 100) 하나다. 학습률은 100 epoch 에 맞춰 줄고, mosaic 을 끄는 마무리 10 epoch 는 91~100 으로 옮겨간다."},
}
RUN_NAMES = {"kimchi_v1": "pilot_v1_imgsz1280", "kimchi_v2": "history_v2_imgsz1280", "kimchi_v3": "history_v3_imgsz1280",
             "kimchi_v4": "exp001_v4_imgsz1280"}
# Weight·기록 파일 이름 (kimchi_v1 예비 실험은 보관하지 않음)
SAVE_NAMES = {"kimchi_v2": "history_v2_imgsz1280", "kimchi_v3": "history_v3_imgsz1280", "kimchi_v4": "exp001"}
SPLIT_NOTES = {
    "kimchi_v2": "kimchi_v2 Split(G00 파/고추 구간 분할, G12 가운데 배치 Train, G05 Val)",
    "kimchi_v3": "kimchi_v3 (kimchi_v2 Split + Class 5 기준 개정 라벨: 점을 묶은 BBox·초록 잎맥·흐린 부분 제외)",
    "kimchi_v4": "kimchi_v4 (kimchi_v3 라벨 + G09 마지막 배치 25장 Val — Val 갈변 8 → 75개)",
}


def main():
    ap = argparse.ArgumentParser(description="해상도 개선 실험 (06 Baseline 조건에서 imgsz 변경)")
    ap.add_argument("--exp", default="exp001", choices=sorted(EXPERIMENTS))
    args = ap.parse_args()
    exp = EXPERIMENTS[args.exp]
    CONDITION = dict(tb.BASELINE, **exp["change"])

    dataset_version, counts = tb.precheck()
    if dataset_version not in RUN_NAMES:
        raise RuntimeError(f"모르는 Dataset Version: {dataset_version} (가능: {sorted(RUN_NAMES)})")
    if args.exp != "exp001" and dataset_version != "kimchi_v4":
        raise RuntimeError(f"{args.exp} 는 kimchi_v4 에서만 실행합니다 (지금 {dataset_version}).")
    if args.exp == "exp001":
        run_name = RUN_NAMES[dataset_version]
        save = SAVE_NAMES.get(dataset_version, run_name)
    else:
        run_name = exp.get("run_name", f"{args.exp}_v4_imgsz{CONDITION['imgsz']}")
        save = args.exp
    keep_record = args.exp != "exp001" or dataset_version in SAVE_NAMES   # Weight 보관·조건 기록을 남기는 실행인가
    WEIGHT_DEST = PROJECT_ROOT / "models" / "improved" / f"{save}_best.pt"
    REPORT = PROJECT_ROOT / "reports" / f"{save}_training_condition.md"

    print("=" * 65)
    print(f" [Subject 08] {run_name} (imgsz {CONDITION['imgsz']}, Dataset {dataset_version}, 비교 대상 {exp['compare']})")
    print("=" * 65)
    print(f" Dataset {dataset_version}: train {counts['train']}장 / val {counts['val']}장 (manifest 와 폴더 일치)")
    print(" 조건: " + ", ".join(f"{k}={v}" for k, v in CONDITION.items()))
    if keep_record and WEIGHT_DEST.exists():
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {WEIGHT_DEST} (덮어쓰지 않음)")

    result = train_detector(data_yaml=str(tb.DATA_YAML), project=str(PROJECT_ROOT / "runs"), name=run_name, **CONDITION)
    checks = check_training(result)
    ok = all(passed for passed, _ in checks.values())

    ref = best_epoch_metrics(result["results_csv"])
    if keep_record:
        if ok:
            copy_weight(result["best"], WEIGHT_DEST)
            checks["Weight 별도 보관"] = (WEIGHT_DEST.is_file(), f"`{rel(WEIGHT_DEST)}` (sha256 {sha256_short(WEIGHT_DEST)})")
        notes = [
            "Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 data/yolo/train·val 이 manifest 와 정확히 같은지 확인했다.",
            f"{SPLIT_NOTES[dataset_version]}로 학습했다. Baseline(06) 조건에서 "
            + ", ".join(f"{k} {tb.BASELINE[k]} → {v}" for k, v in exp["change"].items())
            + f" 으로 바꿨다. 비교 대상: {exp['compare']}. "
            "다른 Dataset Version 과는 Val 구성 또는 라벨이 달라 Validation 점수를 직접 비교하지 않는다.",
            "근거: 6일차 H4(작은 이물 FN) · kimchi_v1 예비 실험 pilot_v1_imgsz1280 (mAP50-95 0.351 → 0.519)"
            + (" · exp001(640 → 1280, mAP50-95 0.538 → 0.712)" if args.exp != "exp001" else "")
            + (" · exp002(1280 → 1920, 0.712 → 0.757, best epoch 50)" if args.exp == "exp003" else "") + ".",
        ]
        if exp.get("note"):
            notes.append(exp["note"])
        if ref:
            notes.append(f"참고 — best.pt 가 저장된 epoch {ref['epoch']} 의 학습 중 Validation: "
                         f"P {ref['precision']:.3f} · R {ref['recall']:.3f} · mAP50 {ref['map50']:.3f} · mAP50-95 {ref['map50_95']:.3f}")
        write_condition_report(
            REPORT,
            f"{'데이터 개선 이력' if save.startswith('history') else '개선 실험 ' + save} 학습 조건 (`{run_name}`)",
            {
                "Model": f"YOLO11n (`{CONDITION['model_name']}`, COCO 사전학습 · pretrained=True)",
                "Dataset Version": f"`{dataset_version}`",
                "Train / Val Manifest": f"`manifests/train.csv` {counts['train']}장 (sha256 {sha256_short(tb.MANIFEST_DIR / 'train.csv')}) / "
                                        f"`manifests/val.csv` {counts['val']}장 (sha256 {sha256_short(tb.MANIFEST_DIR / 'val.csv')})",
                "Data 설정": "`configs/dataset.yaml` (Class ID 0~6, Class 4 미사용)",
                "Epoch": CONDITION["epochs"],
                "Batch": CONDITION["batch"],
                "Image Size": CONDITION["imgsz"],
                "Seed": f"{CONDITION['seed']} (deterministic=True)",
                "Optimizer": CONDITION["optimizer"],
                "Learning Rate (lr0)": CONDITION["lr0"],
                "Augmentation": "Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등)",
            },
            result,
            checks,
            notes=notes,
        )

    print("\n-----------------------------------------------------------------")
    print(" [Checks]")
    print("-----------------------------------------------------------------")
    for k, (passed, detail) in checks.items():
        print(f" {'PASS' if passed else 'FAIL'}  {k}: {detail}")
    if ref:
        print(f"\n (참고) best epoch {ref['epoch']}: mAP50 {ref['map50']:.3f} / mAP50-95 {ref['map50_95']:.3f}")
    if keep_record:
        print(f" 기록: {rel(REPORT)}")
    print(f" 걸린 시간: {result['seconds'] // 60}분 {result['seconds'] % 60}초")
    print("=" * 65)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
