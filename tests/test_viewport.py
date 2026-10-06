"""③ Zoom·편집 시험 (확대·이동 좌표 + Undo/Redo).

화면(tkinter) 없이 순수 계산만 시험한다. 두 가지 방법 모두로 실행된다.

    python tests/test_viewport.py
    python -m pytest tests/test_viewport.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.bbox.history import History                                   # noqa: E402
from src.bbox.viewport import MAX_SCALE, MIN_SCALE, Viewport           # noqa: E402


def close(a, b, eps=1e-9):
    return all(abs(x - y) < eps for x, y in zip(a, b))


# ── Viewport ────────────────────────────────────────────────────────────────
def test_identity_default():
    v = Viewport()
    assert v.image_to_canvas(123, 45) == (123, 45)
    assert v.zoom_percent == 100


def test_roundtrip_any_state():
    v = Viewport(scale=2.37, offset_x=-311.5, offset_y=48.25)
    for p in [(0, 0), (800, 600), (12.3, 456.7)]:
        assert close(v.canvas_to_image(*v.image_to_canvas(*p)), p)


def test_zoom_keeps_cursor_point_fixed():
    v = Viewport(scale=0.8, offset_x=20, offset_y=10)
    cx, cy = 300, 200
    before = v.canvas_to_image(cx, cy)
    for _ in range(5):
        v.zoom_in(cx, cy)
    assert close(v.canvas_to_image(cx, cy), before)
    v.zoom_out(cx, cy)
    assert close(v.canvas_to_image(cx, cy), before)


def test_zoom_in_then_out_restores():
    v = Viewport(scale=1.0, offset_x=5, offset_y=7)
    v.zoom_in(100, 100)
    v.zoom_out(100, 100)
    assert close((v.scale, v.offset_x, v.offset_y), (1.0, 5, 7))


def test_zoom_limits():
    v = Viewport()
    for _ in range(100):
        v.zoom_in(0, 0)
    assert v.scale == MAX_SCALE and v.zoom_in(0, 0) is False
    for _ in range(100):
        v.zoom_out(0, 0)
    assert v.scale == MIN_SCALE and v.zoom_out(0, 0) is False


def test_pan():
    v = Viewport(scale=2)
    before = v.canvas_to_image(100, 100)
    v.pan(30, -10)
    after = v.canvas_to_image(130, 90)       # 이미지가 함께 움직였으므로 같은 점
    assert close(before, after)


def test_fit_large_image_centered():
    v = Viewport()
    v.fit(1600, 1200, 800, 800)              # 가로가 기준 → 0.5 배
    assert close((v.scale,), (0.5,))
    x1, y1 = v.image_to_canvas(0, 0)
    x2, y2 = v.image_to_canvas(1600, 1200)
    assert close((x1, x2), (0, 800))
    assert close((y1,), (800 - y2,)) and close((y1,), (100,))              # 위아래 여백 100px 로 같음


def test_fit_small_image_not_enlarged():
    v = Viewport()
    v.fit(200, 100, 800, 600)
    assert v.scale == 1.0
    assert close(v.image_to_canvas(100, 50), (400, 300))   # 가운데


def test_box_to_canvas_and_clamp():
    v = Viewport(scale=2, offset_x=10, offset_y=20)
    assert close(v.box_to_canvas({"x1": 0, "y1": 0, "x2": 100, "y2": 50}), (10, 20, 210, 120))
    assert v.canvas_to_image_clamped(-500, 99999, 800, 600) == (0, 600)


def test_saved_coords_independent_of_zoom():
    """같은 이미지 위치를 다른 배율에서 드래그해도 이미지 좌표는 같다 → 저장 YOLO 좌표 불변."""
    a = Viewport()
    b = Viewport()
    b.zoom_at(3.0, 50, 50)
    b.pan(-40, 25)
    target = (321.0, 210.0)
    assert close(a.canvas_to_image(*a.image_to_canvas(*target)),
                 b.canvas_to_image(*b.image_to_canvas(*target)))


# ── History (Undo / Redo) ───────────────────────────────────────────────────
B1 = {"cls": 2, "x1": 0, "y1": 0, "x2": 10, "y2": 10}
B2 = {"cls": 5, "x1": 20, "y1": 20, "x2": 40, "y2": 40}


def test_undo_redo_basic():
    h, boxes = History(), []
    h.push(boxes); boxes = boxes + [dict(B1)]
    h.push(boxes); boxes = boxes + [dict(B2)]
    boxes = h.undo(boxes); assert boxes == [B1]
    boxes = h.undo(boxes); assert boxes == []
    assert h.undo(boxes) is None
    boxes = h.redo(boxes); assert boxes == [B1]
    boxes = h.redo(boxes); assert boxes == [B1, B2]
    assert h.redo(boxes) is None


def test_new_edit_clears_redo():
    h, boxes = History(), [dict(B1)]
    h.push(boxes); boxes = []
    boxes = h.undo(boxes)
    assert h.can_redo
    h.push(boxes); boxes = boxes + [dict(B2)]
    assert not h.can_redo


def test_snapshot_is_independent_copy():
    h, boxes = History(), [dict(B1)]
    h.push(boxes)
    boxes[0]["x2"] = 999                     # 기록 후 원본을 직접 고쳐도
    assert h.undo(boxes)[0]["x2"] == 10      # 기록은 그대로


def test_duplicate_push_ignored_and_limit():
    h = History(limit=3)
    assert h.push([B1]) is True
    assert h.push([B1]) is False
    for i in range(10):
        h.push([{**B1, "x2": 20 + i}])
    assert len(h) == 3


def test_clear():
    h = History()
    h.push([B1])
    h.clear()
    assert not h.can_undo and not h.can_redo


# ── 스크립트 실행 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        try:
            fn()
            print("PASS", name)
        except AssertionError:
            print("FAIL", name)
            raise SystemExit(1)
    print(f"\nALL OK — {len(tests)}개 통과")