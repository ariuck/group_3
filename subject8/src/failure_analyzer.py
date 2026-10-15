"""모델이 틀린 것을 모아 유형별로 나누고, 원인을 찾기 위한 표와 그림을 만든다 (가이드 예시 6 · 6일차).

실패 유형 (conf 기준 1개, IoU 0.5):
    FN              정답을 놓침
    CLASS_ERROR     위치는 맞고 Class 를 틀림
    FP_DUPLICATE    이미 짝지어진 정답 위에 다른 Class 로 한 번 더 예측 (같은 물체를 두 종류로 봄)
    FP_PARTIAL      정답과 조금 겹치지만 IoU < 0.5 (박스 위치·크기 차이)
    FP_BACKGROUND   근처에 정답이 전혀 없음 (김치·배경을 이물로 봄, 또는 라벨 누락 후보)
"""
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from ultralytics import YOLO

from src.inference import iou, load_gt, match

SIZE_BUCKETS = ((150, "S(<150px)"), (300, "M(150~300px)"), (10 ** 9, "L(>=300px)"))  # 4K 원본 기준 박스 한 변


def size_bucket(px: float) -> str:
    return next(name for limit, name in SIZE_BUCKETS if px < limit)


def box_px(b, w, h) -> float:
    """박스 크기 = sqrt(넓이), 원본 픽셀"""
    return ((b[2] - b[0]) * w * (b[3] - b[1]) * h) ** 0.5


def cause_hint(kind: str, px: float) -> str:
    """규칙 기반 1차 원인 힌트. 최종 원인은 failure_hypothesis.md 에서 사람이 판단한다."""
    if kind == "FP_DUPLICATE":
        return "same_object_two_classes"
    if kind == "FP_BACKGROUND":
        return "background_confusion_or_missing_label"
    if kind == "FP_PARTIAL":
        return "box_position_or_size"
    if px < SIZE_BUCKETS[0][0]:
        return "small_object"
    return "appearance_or_class_confusion"


def collect_failures(model_path, images_dir: Path, labels_dir: Path, meta: Dict[str, Dict],
                     names: Dict[int, str] = None, conf: float = 0.25, imgsz: int = 640):
    """사진 전체를 예측해 (실패 목록, 정답별 결과 목록) 반환. meta: {이미지 파일명: {capture_group, scene_type}}"""
    model = YOLO(str(model_path))
    names = names or model.names
    images = sorted(p for p in Path(images_dir).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    failures, gt_rows = [], []
    for r in model.predict([str(p) for p in images], conf=conf, imgsz=imgsz, stream=True, verbose=False):
        img = Path(r.path)
        h, w = r.orig_shape
        info = meta.get(img.name, {})
        gt = load_gt(Path(labels_dir) / f"{img.stem}.txt")
        preds = [(int(c), float(p), *map(float, b)) for c, p, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxyn)]
        res = match(gt, preds)

        status = {j: ("FN", None, None) for j in res["fn"]}
        for i, (kind, j) in res["pred_kind"].items():
            if j is not None:
                status[j] = (kind, preds[i][0], preds[i][1])
        for j, (c, *b) in enumerate(gt):
            kind, pc, pconf = status[j]
            px = box_px(b, w, h)
            gt_rows.append({"image": img.name, "class_id": c, "result": kind, "size_px": round(px)})
            if kind == "TP":
                continue
            failures.append({
                "image": img.name, "capture_group": info.get("capture_group", ""), "scene_type": info.get("scene_type", ""),
                "failure_type": kind, "gt_class": names[c], "pred_class": names[pc] if pc is not None else "",
                "conf": round(pconf, 3) if pconf is not None else "", "size_px": round(px), "size_bucket": size_bucket(px),
                "best_iou": "", "cause_hint": cause_hint(kind, px),
                "x1": round(b[0], 4), "y1": round(b[1], 4), "x2": round(b[2], 4), "y2": round(b[3], 4),
            })

        for i, (kind, _) in res["pred_kind"].items():
            if kind != "FP":
                continue
            c, p, *b = preds[i]
            best = max((iou(b, g[1:]) for g in gt), default=0.0)
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            center_in_gt = any(g[1] <= cx <= g[3] and g[2] <= cy <= g[4] for g in gt)
            kind = "FP_DUPLICATE" if best >= 0.5 else ("FP_PARTIAL" if best > 0 or center_in_gt else "FP_BACKGROUND")
            px = box_px(b, w, h)
            failures.append({
                "image": img.name, "capture_group": info.get("capture_group", ""), "scene_type": info.get("scene_type", ""),
                "failure_type": kind, "gt_class": "", "pred_class": names[c], "conf": round(p, 3),
                "size_px": round(px), "size_bucket": size_bucket(px), "best_iou": round(best, 2), "cause_hint": cause_hint(kind, px),
                "x1": round(b[0], 4), "y1": round(b[1], 4), "x2": round(b[2], 4), "y2": round(b[3], 4),
            })
    return failures, gt_rows


def recall_by_size(gt_rows: List[Dict], names: Dict[int, str]) -> List[Dict]:
    out = []
    for c in sorted(names):
        rows = [r for r in gt_rows if r["class_id"] == c]
        for _, bucket in SIZE_BUCKETS:
            sub = [r for r in rows if size_bucket(r["size_px"]) == bucket]
            if sub:
                tp = sum(r["result"] == "TP" for r in sub)
                out.append({"class_id": c, "class_name": names[c], "size_bucket": bucket, "gt": len(sub),
                            "tp": tp, "recall": round(tp / len(sub), 3)})
    return out


def box_size_shift(labels_train: Path, labels_val: Path, names: Dict[int, str], w=4848, h=2704) -> List[Dict]:
    """Class 별 정답 박스 크기(중앙값)를 Train 과 Val 에서 비교 — 같은 Class 인데 모습이 다른지 보는 단서"""
    def sizes(folder):
        out = defaultdict(list)
        for p in Path(folder).glob("*.txt"):
            for c, *b in load_gt(p):
                out[c].append(box_px(b, w, h))
        return out
    tr, va = sizes(labels_train), sizes(labels_val)
    rows = []
    for c in sorted(names):
        if tr[c] or va[c]:
            mt = statistics.median(tr[c]) if tr[c] else None
            mv = statistics.median(va[c]) if va[c] else None
            rows.append({"class_id": c, "class_name": names[c], "train_boxes": len(tr[c]), "val_boxes": len(va[c]),
                         "train_median_px": round(mt) if mt else "", "val_median_px": round(mv) if mv else "",
                         "val_to_train": round(mv / mt, 2) if mt and mv else ""})
    return rows


def _tile(img_path: Path, box, label: str, size=160, pad=0.8):
    img = cv2.imread(str(img_path))
    H, W = img.shape[:2]
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2 * W, (y1 + y2) / 2 * H
    half = max((x2 - x1) * W, (y2 - y1) * H) * (1 + pad) / 2
    a, b, c, d = int(max(0, cx - half)), int(max(0, cy - half)), int(min(W, cx + half)), int(min(H, cy + half))
    t = img[b:d, a:c].copy()
    cv2.rectangle(t, (int(x1 * W) - a, int(y1 * H) - b), (int(x2 * W) - a, int(y2 * H) - b), (0, 0, 255), 2)
    t = cv2.resize(t, (size, size))
    for color, th in (((0, 0, 0), 3), ((255, 255, 255), 1)):
        cv2.putText(t, label, (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, th)
    return t


def _grid(tiles, title: str, cols=8, size=160):
    if not tiles:
        tiles = [np.zeros((size, size, 3), np.uint8)]
    while len(tiles) % cols:
        tiles.append(np.zeros((size, size, 3), np.uint8))
    body = np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])
    bar = np.full((30, body.shape[1], 3), 40, np.uint8)
    cv2.putText(bar, title, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return np.vstack([bar, body])


def class_montage(cls: int, name: str, splits: Dict[str, Path], meta: Dict[str, Dict], out_path: Path, n=16, seed=0):
    """같은 Class 의 정답 박스를 Train / Val 에서 n 개씩 잘라 위아래로 비교. splits: {"train": yolo_root/..}"""
    blocks = []
    for split, root in splits.items():
        items = [(p.stem, b) for p in sorted((root / "labels" / split).glob("*.txt")) for c, *b in load_gt(p) if c == cls]
        random.Random(seed).shuffle(items)
        tiles = [_tile(root / "images" / split / f"{stem}.jpg", b, meta.get(f"{stem}.jpg", {}).get("capture_group", ""))
                 for stem, b in items[:n]]
        blocks.append(_grid(tiles, f"class {cls} {name} - {split.upper()} ({len(items)} boxes)"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), np.vstack(blocks), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out_path


def failure_montage(failures: List[Dict], failure_type: str, images_dir: Path, out_path: Path, n=24):
    rows = [f for f in failures if f["failure_type"] == failure_type]
    rows.sort(key=lambda f: -(f["conf"] or 0) if f["conf"] != "" else 0)
    tiles = []
    for f in rows[:n]:
        label = (f"{f['gt_class'][:6]}>{f['pred_class'][:6]}" if f["gt_class"] and f["pred_class"]
                 else (f["pred_class"] or f["gt_class"])[:10]) + (f" {f['conf']}" if f["conf"] != "" else "")
        tiles.append(_tile(Path(images_dir) / f["image"], (f["x1"], f["y1"], f["x2"], f["y2"]), label))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), _grid(tiles, f"{failure_type} ({len(rows)})"), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out_path


def summarize(failures: List[Dict]) -> List[Dict]:
    """실패 유형 × Class 개수"""
    counts = Counter((f["failure_type"], f["gt_class"] or f["pred_class"]) for f in failures)
    return [{"failure_type": k, "class_name": c, "count": n} for (k, c), n in sorted(counts.items())]
