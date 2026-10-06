"""확대(Zoom)·이동(Pan) 좌표 계산.

화면(캔버스) 좌표와 이미지 픽셀 좌표 사이의 변환만 담당하는 순수 계산 모듈이다.
tkinter 에 의존하지 않으므로 화면 없이도 시험할 수 있다.

    canvas = image * scale + offset
    image  = (canvas - offset) / scale

BBox 는 항상 '이미지 픽셀 좌표'로 저장하고, 그릴 때만 캔버스 좌표로 바꾼다.
그래야 확대 배율이 바뀌어도 저장되는 YOLO 좌표가 흔들리지 않는다.
"""

MIN_SCALE = 0.1      # 10 %
MAX_SCALE = 20.0     # 2000 %
ZOOM_STEP = 1.25     # 휠 한 칸 / 버튼 한 번에 곱하는 배율


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Viewport:
    def __init__(self, scale=1.0, offset_x=0.0, offset_y=0.0):
        self.scale = float(scale)
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)

    # ── 좌표 변환 ─────────────────────────────────────────────────────────────
    def image_to_canvas(self, x, y):
        return x * self.scale + self.offset_x, y * self.scale + self.offset_y

    def canvas_to_image(self, cx, cy):
        return (cx - self.offset_x) / self.scale, (cy - self.offset_y) / self.scale

    def box_to_canvas(self, box):
        """{"x1","y1","x2","y2"} (이미지 픽셀) → (cx1, cy1, cx2, cy2) 캔버스 좌표."""
        cx1, cy1 = self.image_to_canvas(box["x1"], box["y1"])
        cx2, cy2 = self.image_to_canvas(box["x2"], box["y2"])
        return cx1, cy1, cx2, cy2

    def canvas_to_image_clamped(self, cx, cy, img_w, img_h):
        """마우스 위치를 이미지 좌표로 바꾸고 이미지 범위 안으로 잘라낸다."""
        x, y = self.canvas_to_image(cx, cy)
        return _clamp(x, 0, img_w), _clamp(y, 0, img_h)

    # ── 확대 / 축소 ──────────────────────────────────────────────────────────
    def zoom_at(self, factor, cx, cy):
        """(cx, cy) 캔버스 지점이 가리키는 이미지 위치를 고정한 채 배율을 바꾼다.

        마우스 휠로 확대할 때 커서 아래의 물체가 제자리에 머무르게 하는 계산.
        실제로 바뀌었으면 True.
        """
        new_scale = _clamp(self.scale * factor, MIN_SCALE, MAX_SCALE)
        if abs(new_scale - self.scale) < 1e-12:
            return False
        ix, iy = self.canvas_to_image(cx, cy)
        self.scale = new_scale
        self.offset_x = cx - ix * new_scale
        self.offset_y = cy - iy * new_scale
        return True

    def zoom_in(self, cx, cy):
        return self.zoom_at(ZOOM_STEP, cx, cy)

    def zoom_out(self, cx, cy):
        return self.zoom_at(1 / ZOOM_STEP, cx, cy)

    @property
    def zoom_percent(self):
        return round(self.scale * 100)

    # ── 이동 / 맞춤 ──────────────────────────────────────────────────────────
    def pan(self, dx, dy):
        """캔버스 기준으로 (dx, dy) 픽셀만큼 이미지를 옮긴다."""
        self.offset_x += dx
        self.offset_y += dy

    def fit(self, img_w, img_h, canvas_w, canvas_h, margin=0):
        """이미지 전체가 캔버스 안에 들어오도록 배율을 정하고 가운데 정렬한다.

        작은 이미지를 억지로 키우지는 않는다(최대 100 %).
        """
        if img_w <= 0 or img_h <= 0 or canvas_w <= 0 or canvas_h <= 0:
            self.reset()
            return
        avail_w = max(1, canvas_w - 2 * margin)
        avail_h = max(1, canvas_h - 2 * margin)
        self.scale = _clamp(min(avail_w / img_w, avail_h / img_h, 1.0), MIN_SCALE, MAX_SCALE)
        self.offset_x = (canvas_w - img_w * self.scale) / 2
        self.offset_y = (canvas_h - img_h * self.scale) / 2

    def reset(self):
        self.scale, self.offset_x, self.offset_y = 1.0, 0.0, 0.0

    def __repr__(self):
        return f"Viewport(scale={self.scale:.4f}, offset=({self.offset_x:.1f}, {self.offset_y:.1f}))"