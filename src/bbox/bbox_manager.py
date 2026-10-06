"""BBox 생성·선택 로직 (화면(Tkinter)과 무관한 순수 함수).

BBox 는 {"cls": 2, "x1":.., "y1":.., "x2":.., "y2":..} 이고, 좌표는 항상 '원본 이미지 픽셀' 기준이다.
화면 좌표 ↔ 원본 좌표 변환은 화면(UI) 쪽에서 하고, 여기서는 원본 좌표만 다룬다.
"""

MIN_DRAG_PX = 5      # 화면에서 이보다 작게 드래그하면 '실수'로 보고 BBox 를 만들지 않는다
MIN_BOX_PX = 4       # 원본 이미지 기준 최소 BBox 크기 (너무 작은 BBox 방지)


def clamp(v, lo, hi):
    """v 를 lo~hi 범위 안으로 가둔다."""
    return max(lo, min(hi, v))


def make_box(cls, ax, ay, bx, by, img_w, img_h):
    """드래그한 두 점(원본 좌표)으로 BBox 를 만든다. 너무 작으면 None.

    ① 이미지 밖으로 나간 부분은 잘라낸다(clamp)  ② 왼쪽 < 오른쪽, 위 < 아래 가 되도록 정렬한다
    ③ 가로나 세로가 MIN_BOX_PX 보다 작으면 BBox 로 인정하지 않는다
    """
    x1, x2 = sorted((clamp(ax, 0, img_w), clamp(bx, 0, img_w)))
    y1, y2 = sorted((clamp(ay, 0, img_h), clamp(by, 0, img_h)))
    if x2 - x1 < MIN_BOX_PX or y2 - y1 < MIN_BOX_PX:
        return None
    return {"cls": cls, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def find_box_at(boxes, x, y):
    """원본 좌표 (x, y) 를 포함하는 BBox 번호. 겹쳐 있으면 가장 작은 것(안쪽 것)을 고른다. 없으면 None."""
    best, best_area = None, None
    for i, b in enumerate(boxes):
        if b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"]:
            area = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
            if best is None or area <= best_area:
                best, best_area = i, area
    return best


def box_problems(box, img_w, img_h, n_classes=7, unused=()):
    """BBox 에서 이상한 점을 한국어 문장 목록으로 돌려준다. 비어 있으면 정상.

    원본 라벨에 있는 이상한 BBox 는 자동으로 고치거나 지우지 않는다 (사람이 보고 판단) — 대신 화면에서 눈에 띄게 알려 주기 위한 검사다.
    """
    out = []
    cls = box["cls"]
    if not 0 <= cls < n_classes:
        out.append(f"Class {cls} 는 0~{n_classes - 1} 범위 밖")
    elif cls in unused:
        out.append(f"Class {cls} 는 이번 프로젝트에서 사용하지 않는 번호")
    if box["x1"] < -0.5 or box["y1"] < -0.5 or box["x2"] > img_w + 0.5 or box["y2"] > img_h + 0.5:
        out.append("이미지 밖으로 나감")
    if box["x2"] - box["x1"] < MIN_BOX_PX or box["y2"] - box["y1"] < MIN_BOX_PX:
        out.append(f"너무 작음 ({MIN_BOX_PX}px 미만)")
    return out
