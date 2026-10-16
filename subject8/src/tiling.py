"""타일링 — 4K 원본을 겹치는 조각으로 잘라 학습하고, 조각별 예측을 원본 좌표로 합쳐 원본 사진 단위로 채점한다.

작은 이물(특히 작은 갈변, 한 변 20~30px)이 1920 으로 줄이면 10px 안팎이 되는 문제(축소 2.5배)를
2×2 조각(축소 약 1.4배)으로 줄이려는 실험용. 채점은 Ultralytics val 과 같은 방식(IoU 0.50~0.95 10단계, ap_per_class).
"""
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
import torch
from torchvision.ops import batched_nms
from ultralytics.utils.metrics import ap_per_class, box_iou

from src.constants import CLASS_NAMES
from src.inference import load_gt

IOUV = torch.linspace(0.5, 0.95, 10)


def tile_windows(w: int, h: int, grid: Tuple[int, int] = (2, 2), overlap: float = 0.2) -> List[Tuple[int, int, int, int]]:
    """[(x0, y0, x1, y1)] 픽셀 창. 이웃 조각은 조각 크기의 overlap 만큼 겹친다"""
    gx, gy = grid
    tw, th = int(round(w / (gx - (gx - 1) * overlap))), int(round(h / (gy - (gy - 1) * overlap)))
    xs = [0] if gx == 1 else [round(i * (w - tw) / (gx - 1)) for i in range(gx)]
    ys = [0] if gy == 1 else [round(i * (h - th) / (gy - 1)) for i in range(gy)]
    return [(x, y, x + tw, y + th) for y in ys for x in xs]


def tile_labels(boxes, win, w, h, min_visible: float = 0.4) -> List[str]:
    """원본 비율 박스 [(cls, x1, y1, x2, y2)] → 조각 YOLO 줄. 조각 안에 보이는 넓이가 min_visible 미만이면 뺀다"""
    x0, y0, x1, y1 = win
    tw, th = x1 - x0, y1 - y0
    lines = []
    for c, bx1, by1, bx2, by2 in boxes:
        ax1, ay1, ax2, ay2 = bx1 * w, by1 * h, bx2 * w, by2 * h
        cx1, cy1, cx2, cy2 = max(ax1, x0), max(ay1, y0), min(ax2, x1), min(ay2, y1)
        if cx2 <= cx1 or cy2 <= cy1:
            continue
        if (cx2 - cx1) * (cy2 - cy1) < min_visible * (ax2 - ax1) * (ay2 - ay1):
            continue
        lines.append(f"{c} {((cx1 + cx2) / 2 - x0) / tw:.6f} {((cy1 + cy2) / 2 - y0) / th:.6f} "
                     f"{(cx2 - cx1) / tw:.6f} {(cy2 - cy1) / th:.6f}")
    return lines


def write_tiles(image_path: Path, label_path: Path, out_images: Path, out_labels: Path, grid=(2, 2), overlap=0.2) -> int:
    """사진 1장 → 조각 사진(JPG 95)·라벨. 만든 조각 수"""
    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]
    boxes = load_gt(label_path)
    for k, win in enumerate(tile_windows(w, h, grid, overlap)):
        stem = f"{image_path.stem}_t{k}"
        x0, y0, x1, y1 = win
        cv2.imwrite(str(out_images / f"{stem}.jpg"), img[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 95])
        (out_labels / f"{stem}.txt").write_text("\n".join(tile_labels(boxes, win, w, h)) + "\n")
    return len(tile_windows(w, h, grid, overlap))


def predict_full(model, img, imgsz: int, tiles=None, conf=0.001, iou=0.7, merge_iou=0.6, max_det=300) -> np.ndarray:
    """원본 사진 예측 → [[x1, y1, x2, y2, conf, cls]] (원본 픽셀). tiles=(grid, overlap) 이면 조각별 예측을 합친다"""
    h, w = img.shape[:2]
    wins = [(0, 0, w, h)] if tiles is None else tile_windows(w, h, *tiles)
    out = []
    for x0, y0, x1, y1 in wins:
        r = model.predict(img[y0:y1, x0:x1], imgsz=imgsz, conf=conf, iou=iou, max_det=max_det, verbose=False)[0]
        b = r.boxes.data.cpu()
        if len(b):
            b[:, [0, 2]] += x0
            b[:, [1, 3]] += y0
            out.append(b)
    if not out:
        return np.zeros((0, 6), np.float32)
    d = torch.cat(out)
    if tiles is not None:   # 겹친 곳의 같은 물체를 하나로
        d = d[batched_nms(d[:, :4], d[:, 4], d[:, 5].long(), merge_iou)][:max_det]
    return d.numpy()


def match_predictions(pred_cls, true_cls, iou) -> np.ndarray:
    """Ultralytics DetectionValidator 와 같은 짝짓기 → (예측 수, 10) 맞음 여부"""
    correct = np.zeros((len(pred_cls), len(IOUV)), bool)
    iou = (iou * (true_cls[:, None] == pred_cls)).numpy()
    for i, thr in enumerate(IOUV.tolist()):
        m = np.array(np.nonzero(iou >= thr)).T
        if len(m):
            if len(m) > 1:
                m = m[iou[m[:, 0], m[:, 1]].argsort()[::-1]]
                m = m[np.unique(m[:, 1], return_index=True)[1]]
                m = m[np.unique(m[:, 0], return_index=True)[1]]
            correct[m[:, 1].astype(int), i] = True
    return correct


def evaluate_full(model, pairs: List[Tuple[Path, Path]], imgsz: int, tiles=None) -> Dict:
    """원본 사진 단위 채점: [(사진, 라벨)] → 전체·Class 별 P·R·mAP50·mAP50-95"""
    stats = {"tp": [], "conf": [], "cls": [], "target": []}
    for img_path, lbl_path in pairs:
        img = cv2.imread(str(img_path))
        h, w = img.shape[:2]
        gt = load_gt(lbl_path)
        tcls = torch.tensor([g[0] for g in gt], dtype=torch.float32)
        tbox = torch.tensor([[g[1] * w, g[2] * h, g[3] * w, g[4] * h] for g in gt], dtype=torch.float32).reshape(-1, 4)
        d = torch.from_numpy(predict_full(model, img, imgsz, tiles))
        stats["target"].append(tcls.numpy())
        if len(d) == 0:
            continue
        correct = match_predictions(d[:, 5], tcls, box_iou(tbox, d[:, :4])) if len(gt) else np.zeros((len(d), 10), bool)
        stats["tp"].append(correct)
        stats["conf"].append(d[:, 4].numpy())
        stats["cls"].append(d[:, 5].numpy())
    tp, conf, pcls = (np.concatenate(stats[k]) for k in ("tp", "conf", "cls"))
    target = np.concatenate(stats["target"])
    _, _, p, r, _, ap, classes, *_ = ap_per_class(tp, conf, pcls, target, names=CLASS_NAMES)
    per_class = {int(c): {"instances": int((target == c).sum()), "precision": float(p[i]), "recall": float(r[i]),
                          "map50": float(ap[i, 0]), "map50_95": float(ap[i].mean())} for i, c in enumerate(classes)}
    return {"images": len(pairs), "instances": int(len(target)), "precision": float(p.mean()), "recall": float(r.mean()),
            "map50": float(ap[:, 0].mean()), "map50_95": float(ap.mean()), "per_class": per_class}
