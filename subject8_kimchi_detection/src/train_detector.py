"""YOLO11 학습 공통 기능. Smoke Test · Baseline · 개선 실험이 모두 이 함수를 쓴다 (가이드 17.2).

같은 함수를 쓰면 "바꾼 변수 하나" 외에는 학습 방식이 똑같다는 것이 보장된다.
"""
import csv
import hashlib
import math
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import torch
import ultralytics
from ultralytics import YOLO

# 학습 중 Loss 가 NaN/inf 인지 확인할 results.csv 칸
LOSS_COLUMNS = ("train/box_loss", "train/cls_loss", "train/dfl_loss", "val/box_loss", "val/cls_loss", "val/dfl_loss")


def rel(path) -> str:
    """기록용 경로: 현재 폴더(프로젝트 루트) 기준 상대경로. 다른 PC 에서도 같은 글이 되도록"""
    try:
        return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def pick_device() -> str:
    return "0" if torch.cuda.is_available() else "cpu"


def train_detector(
    model_name: str,
    data_yaml: str,
    epochs: int,
    imgsz: int,
    batch: int,
    seed: int,
    project: str,
    name: str,
    optimizer: str = "AdamW",
    lr0: float = 0.001,
    workers: int = 8,
    patience: int = 100,
    **extra,
) -> Dict:
    """YOLO 학습 1회. 같은 이름의 실행 폴더가 있으면 멈춘다 (덮어쓰기·이름 자동 변경 방지).

    반환: save_dir, best, last, results_csv, start, end, seconds, optimizer, lr0, device, gpu
    """
    save_dir = Path(project) / name
    if save_dir.exists():
        raise FileExistsError(f"이미 있는 실행 폴더입니다: {save_dir}\n"
                              f"  다른 --name 을 쓰거나, 이전 결과가 필요 없으면 폴더를 지운 뒤 다시 실행하세요.")

    device = pick_device()
    start = datetime.now()
    t0 = time.time()

    model = YOLO(model_name)
    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        seed=seed,
        deterministic=True,
        optimizer=optimizer,
        lr0=lr0,
        workers=workers,
        patience=patience,
        device=device,
        project=project,
        name=name,
        exist_ok=False,
        **extra,
    )

    save_dir = Path(model.trainer.save_dir)
    return {
        "save_dir": save_dir,
        "best": save_dir / "weights" / "best.pt",
        "last": save_dir / "weights" / "last.pt",
        "results_csv": save_dir / "results.csv",
        "start": start,
        "end": datetime.now(),
        "seconds": round(time.time() - t0),
        "optimizer": optimizer,
        "lr0": lr0,
        "device": device,
        "gpu": torch.cuda.get_device_name(0) if device != "cpu" else "CPU",
    }


def check_training(result: Dict) -> Dict:
    """가이드 17.4 의 확인 항목을 자동 점검. {항목: (통과 여부, 설명)}"""
    rows = []
    if result["results_csv"].is_file():
        with result["results_csv"].open(encoding="utf-8") as f:
            rows = [{k.strip(): v for k, v in r.items()} for r in csv.DictReader(f)]

    nan_cells = 0
    for r in rows:
        for col in LOSS_COLUMNS:
            v = r.get(col)
            if v is not None and (v.strip() == "" or not math.isfinite(float(v))):
                nan_cells += 1

    return {
        "best.pt 생성": (result["best"].is_file(), f"`{rel(result['best'])}`"),
        "last.pt 생성": (result["last"].is_file(), f"`{rel(result['last'])}`"),
        "results.csv 생성": (result["results_csv"].is_file(), f"{len(rows)} epoch 기록"),
        "매 Epoch Validation 실행": (bool(rows) and all(r.get("metrics/mAP50(B)") not in (None, "") for r in rows),
                                   "metrics/mAP50(B) 칸이 모든 epoch 에 있음" if rows else "기록 없음"),
        "Loss NaN/inf 없음": (bool(rows) and nan_cells == 0, f"이상 값 {nan_cells}칸"),
    }


def best_epoch_metrics(results_csv: Path) -> Optional[Dict]:
    """results.csv 에서 best.pt 가 저장된 epoch 의 Validation 지표 (참고용 — 공식 평가는 5일차 evaluate)"""
    if not Path(results_csv).is_file():
        return None
    with Path(results_csv).open(encoding="utf-8") as f:
        rows = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(f)]
    if not rows:
        return None
    # Ultralytics 8.4 는 mAP50-95 가 가장 높은 epoch 을 best.pt 로 저장한다 (fitness 가중치 [0, 0, 0, 1])
    best = max(rows, key=lambda r: float(r["metrics/mAP50-95(B)"]))
    return {
        "epoch": int(float(best["epoch"])),
        "precision": float(best["metrics/precision(B)"]),
        "recall": float(best["metrics/recall(B)"]),
        "map50": float(best["metrics/mAP50(B)"]),
        "map50_95": float(best["metrics/mAP50-95(B)"]),
    }


def copy_weight(src: Path, dest: Path) -> Path:
    """runs/.../best.pt 를 역할이 보이는 이름으로 별도 보관 (예: models/baseline/baseline_best.pt)"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError(f"이미 보관된 Weight 가 있습니다: {dest} (덮어쓰지 않음)")
    shutil.copy2(src, dest)
    return dest


def sha256_short(path: Path, n: int = 12) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def versions() -> Dict[str, str]:
    return {"ultralytics": ultralytics.__version__, "torch": torch.__version__,
            "cuda": torch.version.cuda or "-"}


def write_condition_report(path: Path, title: str, condition: Dict, result: Dict, checks: Dict,
                           notes: Optional[list] = None) -> Path:
    """학습 조건·환경·점검 결과를 Markdown 으로 남긴다 (baseline_training_condition.md, 실험 기록 등)."""
    v = versions()
    peak = f"{torch.cuda.max_memory_allocated() / 1024 ** 3:.1f} GB" if torch.cuda.is_available() else "-"
    lines = [f"# {title}", "",
             f"> 자동 생성: `{Path(__file__).name}` · {result['end']:%Y-%m-%d %H:%M}", "",
             "## 학습 조건", "", "| 항목 | 값 |", "|---|---|"]
    lines += [f"| {k} | {val} |" for k, val in condition.items()]
    lines += ["", "## 실행 환경", "", "| 항목 | 값 |", "|---|---|",
              f"| GPU | {result['gpu']} (device {result['device']}) |",
              f"| GPU 최대 사용 메모리 | {peak} |",
              f"| Ultralytics | {v['ultralytics']} |",
              f"| PyTorch / CUDA | {v['torch']} / {v['cuda']} |",
              f"| 학습 시작 | {result['start']:%Y-%m-%d %H:%M:%S} |",
              f"| 학습 종료 | {result['end']:%Y-%m-%d %H:%M:%S} |",
              f"| 걸린 시간 | {result['seconds'] // 60}분 {result['seconds'] % 60}초 |",
              f"| 실행 폴더 | `{rel(result['save_dir'])}` |",
              "", "## 학습 점검 (가이드 17.4)", "", "| 항목 | 결과 | 내용 |", "|---|:---:|---|"]
    lines += [f"| {k} | {'✅' if ok else '❌'} | {detail} |" for k, (ok, detail) in checks.items()]
    if notes:
        lines += ["", "## 메모", ""] + [f"- {n}" for n in notes]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
