"""BBox 이동 · 크기 조절 계산 (화면(Tkinter)과 무관한 순수 함수).

BBox 는 {"cls": 2, "x1":.., "y1":.., "x2":.., "y2":..} 이고 좌표는 항상 '원본 이미지 픽셀' 기준이다.
이 모듈의 함수는 새 BBox 사본을 돌려줄 뿐 원본 dict 를 고치지 않는다. (취소할 때 원래 값이 그대로 남아 있어야 하므로)

핸들 이름은 나침반 방향이다:      nw ── n ── ne
                                  │          │
                                  w          e
                                  │          │
                                  sw ── s ── se
"""
from src.bbox.bbox_manager import MIN_BOX_PX, clamp

HANDLE_NAMES = ("nw", "n", "ne", "e", "se", "s", "sw", "w")

# Tk 커서 이름 (X11/WSL 에서 쓸 수 있는 이름 — Windows 의 Tk 도 대부분 지원한다)
HANDLE_CURSORS = {
    "nw": "top_left_corner", "ne": "top_right_corner",
    "sw": "bottom_left_corner", "se": "bottom_right_corner",
    "n": "sb_v_double_arrow", "s": "sb_v_double_arrow",
    "e": "sb_h_double_arrow", "w": "sb_h_double_arrow",
}


def handle_points(box):
    """8개 핸들의 위치 {이름: (x, y)} (원본 픽셀)."""
    x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
    xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
    return {"nw": (x1, y1), "n": (xm, y1), "ne": (x2, y1), "e": (x2, ym),
            "se": (x2, y2), "s": (xm, y2), "sw": (x1, y2), "w": (x1, ym)}


def hit_handle(box, x, y, tol):
    """(x, y) 가 핸들 근처(tol 픽셀 이내)면 그 핸들 이름, 아니면 None. 여러 개면 가장 가까운 것."""
    best, best_d = None, None
    for name, (hx, hy) in handle_points(box).items():
        d = max(abs(hx - x), abs(hy - y))
        if d <= tol and (best is None or d < best_d):
            best, best_d = name, d
    return best


def move_box(box, dx, dy, img_w, img_h):
    """BBox 를 (dx, dy) 만큼 옮긴다. 크기는 그대로, 이미지 밖으로는 나가지 않는다."""
    w, h = box["x2"] - box["x1"], box["y2"] - box["y1"]
    x1 = clamp(box["x1"] + dx, 0, max(0.0, img_w - w))
    y1 = clamp(box["y1"] + dy, 0, max(0.0, img_h - h))
    return {**box, "x1": x1, "y1": y1, "x2": x1 + w, "y2": y1 + h}


def resize_box(box, handle, x, y, img_w, img_h, min_size=MIN_BOX_PX):
    """handle 을 마우스 위치 (x, y) 로 끌었을 때의 새 BBox.

    · 끄는 변만 움직이고 반대쪽 변은 고정  · 이미지 밖으로 못 나감  · 가로·세로 최소 min_size 픽셀
    """
    x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
    x, y = clamp(x, 0, img_w), clamp(y, 0, img_h)
    if "w" in handle:
        x1 = min(x, x2 - min_size)
    if "e" in handle:
        x2 = max(x, x1 + min_size)
    if "n" in handle:
        y1 = min(y, y2 - min_size)
    if "s" in handle:
        y2 = max(y, y1 + min_size)
    # 이미지 가장자리에 붙은 작은 BBox 를 키우면 반대쪽이 밖으로 나갈 수 있어 한 번 더 안으로 넣는다
    if x2 > img_w:
        x2, x1 = img_w, min(x1, img_w - min_size)
    if y2 > img_h:
        y2, y1 = img_h, min(y1, img_h - min_size)
    return {**box, "x1": max(0.0, x1), "y1": max(0.0, y1), "x2": x2, "y2": y2}
