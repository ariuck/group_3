"""학습된 Weight 의 검출 성능을 숫자로 측정한다 (가이드 18.1). Baseline · 개선 실험 · Final 이 모두 이 함수를 쓴다.

Frozen Test 는 Final Model 을 정한 뒤 8일차에 한 번만 쓴다. 그래서 split="test" 는 allow_test=True 일 때만 허용한다.
"""
from pathlib import Path
from typing import Dict

import yaml
from ultralytics import YOLO

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def count_split_images(data_yaml, split: str) -> int:
    """dataset.yaml 의 path/<split> 폴더 사진 수 (상대 path 는 현재 폴더 기준)"""
    cfg = yaml.safe_load(Path(data_yaml).read_text(encoding="utf-8"))
    folder = Path(cfg.get("path", ".")) / cfg[split]
    return sum(1 for p in folder.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES) if folder.is_dir() else 0


def evaluate_detector(model_path, data_yaml, split: str, imgsz: int, batch: int = 16,
                      project="runs", name="eval", allow_test: bool = False) -> Dict:
    """model.val() 로 평가 → 전체·Class별 지표 dict. 그래프(PR 곡선, Confusion Matrix)는 project/name 에 저장"""
    if split == "test" and not allow_test:
        raise PermissionError("Frozen Test 는 Final Model 확정 후 8일차에만 평가합니다 (allow_test=True 필요).")
    if split not in ("train", "val", "test"):
        raise ValueError(f"split 은 train / val / test 중 하나: {split}")
    if not Path(model_path).is_file():
        raise FileNotFoundError(f"Weight 가 없습니다: {model_path}")

    model = YOLO(str(model_path))
    m = model.val(data=str(data_yaml), split=split, imgsz=imgsz, batch=batch,
                  plots=True, project=str(project), name=name, exist_ok=True, verbose=False)

    names = m.names
    per_class = []
    evaluated = {int(c): i for i, c in enumerate(m.box.ap_class_index)}
    for cid in sorted(names):
        row = {"class_id": cid, "class_name": names[cid],
               "images": int(m.nt_per_image[cid]), "instances": int(m.nt_per_class[cid])}
        if cid in evaluated:
            p, r, ap50, ap = m.box.class_result(evaluated[cid])
            row.update(precision=round(float(p), 4), recall=round(float(r), 4),
                       map50=round(float(ap50), 4), map50_95=round(float(ap), 4), note="")
        else:
            # 정답이 0건이면 Recall·AP 를 계산할 수 없다 (Class 4 미사용 등)
            row.update(precision="", recall="", map50="", map50_95="", note="Instance 0건 — 평가 불가")
        per_class.append(row)

    return {
        "split": split,
        "images": count_split_images(data_yaml, split),
        "instances": int(m.nt_per_class.sum()),
        "precision": round(float(m.box.mp), 4),
        "recall": round(float(m.box.mr), 4),
        "map50": round(float(m.box.map50), 4),
        "map50_95": round(float(m.box.map), 4),
        "per_class": per_class,
        "save_dir": Path(m.save_dir),
        "speed_ms": {k: round(v, 1) for k, v in m.speed.items()},
    }
