"""학습된 Weight 로 사진을 예측하고, 정답(GT)과 비교해 맞힘·놓침·오검출을 사진 단위로 센다 (가이드 18장 · 6일차 실패분석 준비).

비교 규칙 (IoU 0.5 기준):
    TP           같은 Class 이고 박스가 IoU ≥ 0.5 로 겹침         → 맞힘
    CLASS_ERROR  박스는 IoU ≥ 0.5 로 겹치는데 Class 가 다름      → 종류를 틀림
    FP           어떤 정답과도 겹치지 않는 예측                    → 없는 이물을 있다고 함
    FN           어떤 예측과도 겹치지 않는 정답                    → 이물을 놓침
"""
from pathlib import Path
from typing import Dict, List, Tuple

import cv2

IOU_THRESHOLD = 0.5
# Class 별 색 (BGR). 같은 Class 는 GT·예측 모두 같은 색
COLORS = {0: (60, 180, 75), 1: (230, 50, 50), 2: (0, 130, 200), 3: (255, 225, 25),
          4: (128, 128, 128), 5: (145, 30, 180), 6: (245, 130, 48)}

Box = Tuple[int, float, float, float, float]  # class_id, x1, y1, x2, y2 (0~1 비율)


def load_gt(label_path: Path) -> List[Box]:
    """YOLO TXT → [(cls, x1, y1, x2, y2)] (비율 좌표). 파일이 없으면 빈 목록"""
    boxes = []
    if not Path(label_path).is_file():
        return boxes
    for line in Path(label_path).read_text(encoding="utf-8-sig").splitlines():
        p = line.split()
        if len(p) != 5:
            continue
        c, x, y, w, h = int(p[0]), *map(float, p[1:])
        boxes.append((c, x - w / 2, y - h / 2, x + w / 2, y + h / 2))
    return boxes


def iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def match(gt: List[Box], preds: List[Tuple[int, float, float, float, float, float]]) -> Dict:
    """preds: [(cls, conf, x1, y1, x2, y2)]. 확신이 높은 예측부터 정답과 짝짓는다."""
    order = sorted(range(len(preds)), key=lambda i: -preds[i][1])
    gt_used, pred_kind = set(), {}

    # 1차: 같은 Class 끼리 (TP)
    for i in order:
        c, _, *pb = preds[i]
        best, bj = IOU_THRESHOLD, None
        for j, (gc, *gb) in enumerate(gt):
            if j not in gt_used and gc == c and iou(pb, gb) >= best:
                best, bj = iou(pb, gb), j
        if bj is not None:
            gt_used.add(bj)
            pred_kind[i] = ("TP", bj)

    # 2차: 남은 것 중 위치는 맞는데 Class 가 다른 것 (CLASS_ERROR)
    for i in order:
        if i in pred_kind:
            continue
        _, _, *pb = preds[i]
        best, bj = IOU_THRESHOLD, None
        for j, (_, *gb) in enumerate(gt):
            if j not in gt_used and iou(pb, gb) >= best:
                best, bj = iou(pb, gb), j
        if bj is not None:
            gt_used.add(bj)
            pred_kind[i] = ("CLASS_ERROR", bj)

    for i in range(len(preds)):
        pred_kind.setdefault(i, ("FP", None))
    fn = [j for j in range(len(gt)) if j not in gt_used]
    kinds = [k for k, _ in pred_kind.values()]
    return {"pred_kind": pred_kind, "fn": fn,
            "tp": kinds.count("TP"), "class_error": kinds.count("CLASS_ERROR"),
            "fp": kinds.count("FP"), "fn_count": len(fn)}


def draw_comparison(image_path: Path, gt: List[Box], preds, result: Dict, names: Dict, out_path: Path,
                    max_width: int = 1600) -> Path:
    """왼쪽 = 정답(GT), 오른쪽 = 예측. 예측은 TP 실선 / CLASS_ERROR 노랑 테두리 / FP 빨강 테두리, 놓친 GT 는 왼쪽에 빨강 X"""
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")
    scale = min(1.0, max_width / img.shape[1])
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    left, right = img.copy(), img.copy()
    thick = max(2, w // 500)

    def px(b):
        return int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)

    def label(canvas, text, x, y, color):
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y = max(th + 4, y)
        cv2.rectangle(canvas, (x, y - th - 4), (x + tw + 4, y), color, -1)
        cv2.putText(canvas, text, (x + 2, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    missed = set(result["fn"])
    for j, (c, *b) in enumerate(gt):
        x1, y1, x2, y2 = px(b)
        cv2.rectangle(left, (x1, y1), (x2, y2), COLORS.get(c, (255, 255, 255)), thick)
        label(left, f"{c} {names.get(c, c)}", x1, y1, COLORS.get(c, (255, 255, 255)))
        if j in missed:  # 놓친 정답
            cv2.line(left, (x1, y1), (x2, y2), (0, 0, 255), thick)
            cv2.line(left, (x1, y2), (x2, y1), (0, 0, 255), thick)

    for i, (c, conf, *b) in enumerate(preds):
        kind, _ = result["pred_kind"][i]
        x1, y1, x2, y2 = px(b)
        color = COLORS.get(c, (255, 255, 255))
        cv2.rectangle(right, (x1, y1), (x2, y2), color, thick)
        if kind != "TP":  # 틀린 예측은 바깥 테두리로 표시
            edge = (0, 0, 255) if kind == "FP" else (0, 255, 255)
            cv2.rectangle(right, (x1 - thick * 2, y1 - thick * 2), (x2 + thick * 2, y2 + thick * 2), edge, thick)
        label(right, f"{c} {names.get(c, c)} {conf:.2f}{'' if kind == 'TP' else ' ' + kind}", x1, y1, color)

    for canvas, title in ((left, f"GT {len(gt)}"),
                          (right, f"PRED {len(preds)}  TP {result['tp']}  CLS_ERR {result['class_error']}  "
                                  f"FP {result['fp']}  FN {result['fn_count']}")):
        cv2.rectangle(canvas, (0, 0), (w, 34), (0, 0, 0), -1)
        cv2.putText(canvas, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), cv2.hconcat([left, right]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out_path
