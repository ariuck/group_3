"""공식 Version kimchi_v5 (C안 재분할) 학습 — 06 Baseline 조건 + 한 변수 개선 실험을 v5 에서 한다.

    python scripts/00_setup.py                       # 먼저 data/yolo (v5) 준비
    python scripts/11_train_v5.py --run exp001       # 하나만 (all = 차례로 전부, 이미 Weight 가 있으면 멈춤)
    python scripts/11_train_v5.py --run exp005 --report-only   # 학습은 끝났는데 조건 기록만 다시

  baseline : imgsz 640                         → runs/baseline_v5/
  exp001   : imgsz 1280                        → runs/exp001_v5_imgsz1280/
  exp002   : imgsz 1920 · batch 6              → runs/exp002_v5_imgsz1920/
  exp003   : exp002 + epochs 100               → runs/exp003_v5_imgsz1920_epoch100/
  exp005   : exp002 + 증강 (flipud · hsv_v)    → runs/exp005_v5_imgsz1920_aug/
  (exp004 타일링은 14_train_tiles_v5.py)
  Weight → models/baseline · improved/<실행>.pt (src/registry.py)
  조건 기록 → reports/02_baseline/baseline_training_condition.md (baseline), reports/04_improvement/<실행>_training_condition.md

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
os.chdir(PROJECT_ROOT)  # dataset.yaml 의 path: data/yolo 는 이 폴더 기준

from src import registry  # noqa: E402
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

_EXP007 = {"model_name": "yolo11s.pt", "imgsz": 1920, "batch": 3, "flipud": 0.5, "hsv_v": 0.6}   # exp007 조건 (v5 Val 최고 0.724)
_AUG_TEXT = "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp007 과 같음"
RUNS = {
    "baseline": {"change": {}, "run_name": "baseline_v5", "title": "kimchi_v5 Baseline"},
    "exp001": {"change": ex.EXPERIMENTS["exp001"]["change"], "run_name": "exp001_v5_imgsz1280",
               "title": "kimchi_v5 개선 실험 exp001", "compare": "baseline_v5 (imgsz 640)"},
    "exp002": {"change": ex.EXPERIMENTS["exp002"]["change"], "run_name": "exp002_v5_imgsz1920",
               "title": "kimchi_v5 개선 실험 exp002", "compare": "exp001_v5 (imgsz 1280)",
               "note": ex.EXPERIMENTS["exp002"]["note"]},
    "exp003": {"change": ex.EXPERIMENTS["exp003"]["change"], "run_name": "exp003_v5_imgsz1920_epoch100",
               "title": "kimchi_v5 개선 실험 exp003", "compare": "exp002_v5 (epochs 50)",
               "note": ex.EXPERIMENTS["exp003"]["note"]},
    # 바꾸는 변수 하나 = 증강 설정 (가이드 참고자료 "Augmentation: 기본 → 밝기/Scale 등 강화")
    # 근거: v5 Val 은 Train 이 못 본 촬영 묶음(다른 날·다른 조명) — exp002_v5 는 Train loss 가 계속 내려가는데 Val dfl_loss 는 30 epoch 뒤 멈춤(과적합 신호)
    #   flipud 0 → 0.5 : 위에서 내려다본 사진이라 위아래 뒤집어도 같은 장면 (이물 방향은 원래 제각각)
    #   hsv_v 0.4 → 0.6: 날짜마다 다른 밝기
    "exp005": {"change": {**ex.EXPERIMENTS["exp002"]["change"], "flipud": 0.5, "hsv_v": 0.6},
               "run_name": "exp005_v5_imgsz1920_aug",
               "title": "kimchi_v5 개선 실험 exp005", "compare": "exp002_v5 (기본 증강)",
               "augmentation": "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4)",
               "note": "exp002_v5 와 다른 변수는 증강 설정 하나 (flipud 0 → 0.5, hsv_v 0.4 → 0.6). 이미지 파일은 만들지 않고 학습 중에만 변형한다. Val 은 원본."},
    # 두 변수 동시 변경 실험 (사용자 결정 2026-10-16) — exp002 대비 2개, exp005(증강) 대비는 1개라 각 효과를 따로 읽는다.
    # RTX 3060 12GB 측정: 11n·2560·batch 3 = 10.8GB, 11s·1920·batch 3 = 9.0GB (11s·2560 은 batch 2 도 13.6GB 로 넘쳐 제외)
    "exp006": {"change": {"imgsz": 2560, "batch": 3, "flipud": 0.5, "hsv_v": 0.6},
               "run_name": "exp006_v5_imgsz2560_aug", "title": "kimchi_v5 개선 실험 exp006",
               "compare": "exp005_v5 (imgsz 1920 · 같은 증강) — exp002_v5 대비로는 해상도·증강 두 변수",
               "augmentation": "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp005 와 같음",
               "note": "exp005_v5 와 다른 변수는 imgsz(1920 → 2560) 하나 (batch 6 → 3 은 GPU 메모리 때문, nbs=64 gradient 누적으로 갱신 1번당 사진 수는 거의 같음). "
                       "exp002_v5 대비로는 해상도·증강 두 변수를 함께 바꾼 실험이다."},
    "exp007": {"change": {"model_name": "yolo11s.pt", "imgsz": 1920, "batch": 3, "flipud": 0.5, "hsv_v": 0.6},
               "run_name": "exp007_v5_s_imgsz1920_aug", "title": "kimchi_v5 개선 실험 exp007",
               "compare": "exp005_v5 (YOLO11n · 같은 증강) — exp002_v5 대비로는 모델 크기·증강 두 변수",
               "augmentation": "기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp005 와 같음",
               "note": "exp005_v5 와 다른 변수는 모델 크기(YOLO11n → YOLO11s) 하나 (batch 6 → 3 은 GPU 메모리 때문). "
                       "exp002_v5 대비로는 모델 크기·증강 두 변수를 함께 바꾼 실험이다."},
    # ── 3대 분산 실험 (docs/project/experiment_handoff.md) — 모두 exp007(11s · 1920 · 증강) 기준, 한 변수씩 ──
    "exp008": {"change": {**_EXP007, "epochs": 100}, "run_name": "exp008_v5_s_imgsz1920_aug_epoch100",
               "title": "kimchi_v5 개선 실험 exp008", "compare": "exp007_v5 (epochs 50)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 epochs(50 → 100) 하나. exp007 의 best epoch 가 마지막(50)이라 학습 부족 가능성 확인."},
    "exp009": {"change": {**_EXP007, "model_name": "yolo11m.pt", "batch": 2}, "run_name": "exp009_v5_m_imgsz1920_aug",
               "title": "kimchi_v5 개선 실험 exp009", "compare": "exp007_v5 (YOLO11s)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 모델 크기(YOLO11s → YOLO11m) 하나 (batch 3 → 2 는 GPU 메모리 — 12GB 에서 넘치면 batch 1 대신 GPU 큰 PC 에서)."},
    "exp011": {"change": {k: v for k, v in _EXP007.items() if k not in ("flipud", "hsv_v")}, "run_name": "exp011_v5_s_imgsz1920",
               "title": "kimchi_v5 개선 실험 exp011", "compare": "exp007_v5 (증강 있음)",
               "note": "exp007_v5 와 다른 변수는 증강 하나 (flipud·hsv_v 를 기본값으로). 큰 모델에서 증강이 실제로 도움이 되는지 분리."},
    "exp012": {"change": {**_EXP007, "imgsz": 1280, "batch": 6}, "run_name": "exp012_v5_s_imgsz1280_aug",
               "title": "kimchi_v5 개선 실험 exp012", "compare": "exp007_v5 (imgsz 1920)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 imgsz(1920 → 1280) 하나 (batch 3 → 6). 예측 속도가 중요한 현장(교과 14)용 가벼운 후보."},
    "exp013": {"change": {**_EXP007, "seed": 7}, "run_name": "exp013_v5_s_imgsz1920_aug_seed7",
               "title": "kimchi_v5 반복 실험 exp013", "compare": "exp007_v5 (seed 42)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 seed 만 다르다 (42 → 7). 같은 조건에서 점수가 얼마나 흔들리는지 재서, 실험 사이 0.02 차이가 의미 있는지 판단한다."},
    # ── 2라운드 (Final 후보 3개 × seed 2개 — docs/project/experiment_handoff.md 8장) ──
    # exp013 결과 seed 만 바꿔도 ±0.01 흔들림 → 후보마다 seed 2개 이상 평균으로 비교한다
    "exp014": {"change": {**_EXP007, "seed": 123}, "run_name": "exp014_v5_s_imgsz1920_aug_seed123",
               "title": "kimchi_v5 반복 실험 exp014", "compare": "exp007_v5 · exp013_v5 (같은 조건 seed 42 · 7)", "augmentation": _AUG_TEXT,
               "note": "exp007 조건의 세 번째 seed (123). 후보 A(11s · 1920) 의 seed 평균·흔들림을 잰다."},
    "exp015": {"change": {**_EXP007, "imgsz": 2240, "batch": 2}, "run_name": "exp015_v5_s_imgsz2240_aug",
               "title": "kimchi_v5 개선 실험 exp015", "compare": "exp007_v5 (imgsz 1920)", "augmentation": _AUG_TEXT,
               "note": "exp007_v5 와 다른 변수는 imgsz(1920 → 2240) 하나 (batch 3 → 2, GPU 9.4GB 측정). 11n 에서 해상도 효과가 컸고(+0.038), 11s·2560 은 메모리 초과라 2240."},
    "exp016": {"change": {**_EXP007, "imgsz": 2240, "batch": 2, "seed": 7}, "run_name": "exp016_v5_s_imgsz2240_aug_seed7",
               "title": "kimchi_v5 반복 실험 exp016", "compare": "exp015_v5 (seed 42)", "augmentation": _AUG_TEXT,
               "note": "exp015 조건의 두 번째 seed (7). 후보 B(11s · 2240) 의 seed 평균."},
    "exp017": {"change": {**_EXP007, "model_name": "yolo11m.pt", "batch": 2, "seed": 7}, "run_name": "exp017_v5_m_imgsz1920_aug_seed7",
               "title": "kimchi_v5 반복 실험 exp017", "compare": "exp009_v5 (seed 42)", "augmentation": _AUG_TEXT,
               "note": "exp009 조건(YOLO11m · 1920 · batch 2, GPU 9.8GB 측정)의 두 번째 seed (7). 후보 C(11m · 1920) 의 seed 평균."},
    "exp018": {"change": {**_EXP007, "imgsz": 2240, "batch": 2, "seed": 123}, "run_name": "exp018_v5_s_imgsz2240_aug_seed123",
               "title": "kimchi_v5 반복 실험 exp018", "compare": "exp015_v5 · exp016_v5 (같은 조건 seed 42 · 7)", "augmentation": _AUG_TEXT,
               "note": "exp015 조건(11s · 2240 · batch 2)의 세 번째 seed (123). 후보 B 를 후보 A(exp007·013·014) 와 같은 seed 3개 평균으로 비교한다."},
}
REPORT_DIR = PROJECT_ROOT / "reports" / "04_improvement"
BASELINE_REPORT = PROJECT_ROOT / "reports" / "02_baseline" / "baseline_training_condition.md"   # 가이드 이름 (산출물 2)
# 06 BASELINE 에 없는 증강 값의 Ultralytics 8.4 기본값 (조건 기록에 "기본 → 바꾼 값" 으로 적는다)
ULTRALYTICS_DEFAULTS = {"flipud": 0.0, "fliplr": 0.5, "hsv_h": 0.015, "hsv_s": 0.7, "hsv_v": 0.4, "degrees": 0.0,
                        "translate": 0.1, "scale": 0.5, "mosaic": 1.0, "mixup": 0.0}


def finished_result(run_name):
    """이미 끝난 실행의 결과 dict (조건 기록만 다시 쓸 때) — 시작 = args.yaml, 종료 = results.csv 수정 시각"""
    import torch
    from datetime import datetime
    d = PROJECT_ROOT / "runs" / run_name
    start = datetime.fromtimestamp((d / "args.yaml").stat().st_mtime)
    end = datetime.fromtimestamp((d / "results.csv").stat().st_mtime)
    return {"save_dir": d, "best": d / "weights" / "best.pt", "last": d / "weights" / "last.pt",
            "results_csv": d / "results.csv", "start": start, "end": end, "seconds": round((end - start).total_seconds()),
            "optimizer": tb.BASELINE["optimizer"], "lr0": tb.BASELINE["lr0"], "device": 0,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"}


def train_one(key, counts, report_only=False):
    spec = RUNS[key]
    cond = dict(tb.BASELINE, **spec["change"])
    run_name = spec["run_name"]
    weight = registry.weight_path(run_name)
    report = BASELINE_REPORT if key == "baseline" else REPORT_DIR / f"{run_name}_training_condition.md"
    if weight.exists() and not report_only:
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {weight} (덮어쓰지 않음)")
    print("=" * 65)
    print(f" [Subject 08] {run_name} (Dataset {DATASET_VERSION})" + (" — 조건 기록만" if report_only else ""))
    print("=" * 65)
    print(" 조건: " + ", ".join(f"{k}={v}" for k, v in cond.items()))

    if report_only:
        result = finished_result(run_name)
    else:
        result = train_detector(data_yaml=str(paths.dataset_yaml), project=str(PROJECT_ROOT / "runs"), name=run_name, **cond)
    checks = check_training(result)
    ok = all(passed for passed, _ in checks.values())
    if ok:
        if not weight.exists():
            copy_weight(result["best"], weight)
        checks["Weight 별도 보관"] = (weight.is_file(), f"`{rel(weight)}` (sha256 {sha256_short(weight)})")

    ref = best_epoch_metrics(result["results_csv"])
    notes = [
        f"Frozen Test 와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `{rel(paths.yolo_dir)}/train·val` 이 manifest 와 정확히 같은지 확인했다.",
        "kimchi_v5 = C안 재분할(묶음 통째 배정, 예외는 G00 하나) + 라벨 수정본 kimchi_v5(v3 + 이물 없는 박스 3개 삭제). "
        "기준: `docs/project/kimchi_v5_split.md`. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.",
    ]
    if spec["change"]:
        notes.append("Baseline(06) 조건에서 " + ", ".join(f"{k} {tb.BASELINE.get(k, ULTRALYTICS_DEFAULTS.get(k))} → {v}"
                                                         for k, v in spec["change"].items())
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
            "Model": f"YOLO{Path(cond['model_name']).stem[4:]} (`{cond['model_name']}`, COCO 사전학습 · pretrained=True)",
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
            "Augmentation": spec.get("augmentation", "Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등)"),
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
    ap = argparse.ArgumentParser(description="kimchi_v5 학습 (baseline · exp001~005)")
    ap.add_argument("--run", default="all", choices=["all", *RUNS])
    ap.add_argument("--report-only", action="store_true", help="학습은 끝났는데 조건 기록이 없을 때 기록만 다시 쓴다")
    args = ap.parse_args()
    dataset_version, counts = tb.precheck()
    if dataset_version != DATASET_VERSION:
        raise RuntimeError(f"{rel(paths.yolo_dir)} 가 {dataset_version} 입니다.\n"
                           f"  python scripts/03_build_split.py --version {DATASET_VERSION} --copy-files")
    print(f" Dataset {dataset_version}: train {counts['train']}장 / val {counts['val']}장 (manifest 와 폴더 일치)")
    for key in (RUNS if args.run == "all" else [args.run]):
        if not train_one(key, counts, args.report_only):
            sys.exit(1)


if __name__ == "__main__":
    main()
