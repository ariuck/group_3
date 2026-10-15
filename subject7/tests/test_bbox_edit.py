"""BBox 이동·크기 조절 계산 시험 (화면 없이).

실행 (프로젝트 폴더에서):  python -m unittest tests/test_bbox_edit.py
"""
import unittest

from src.bbox.bbox_edit import HANDLE_CURSORS, HANDLE_NAMES, handle_points, hit_handle, move_box, resize_box
from src.bbox.bbox_manager import MIN_BOX_PX

W, H = 1000, 800
BOX = {"cls": 2, "x1": 100.0, "y1": 200.0, "x2": 300.0, "y2": 400.0}


class HandleTest(unittest.TestCase):
    def test_eight_handles_with_cursors(self):
        pts = handle_points(BOX)
        self.assertEqual(set(pts), set(HANDLE_NAMES))
        self.assertEqual(set(HANDLE_CURSORS), set(HANDLE_NAMES))
        self.assertEqual(pts["nw"], (100.0, 200.0))
        self.assertEqual(pts["se"], (300.0, 400.0))
        self.assertEqual(pts["n"], (200.0, 200.0))
        self.assertEqual(pts["e"], (300.0, 300.0))

    def test_hit_within_tolerance(self):
        self.assertEqual(hit_handle(BOX, 103, 198, 5), "nw")
        self.assertEqual(hit_handle(BOX, 299, 305, 8), "e")
        self.assertIsNone(hit_handle(BOX, 200, 300, 5))           # 한가운데는 핸들이 아니다

    def test_nearest_handle_wins_on_a_tiny_box(self):
        tiny = {"cls": 0, "x1": 100.0, "y1": 100.0, "x2": 106.0, "y2": 106.0}
        self.assertEqual(hit_handle(tiny, 101, 101, 8), "nw")
        self.assertEqual(hit_handle(tiny, 105, 105, 8), "se")


class MoveTest(unittest.TestCase):
    def test_move_keeps_size_and_does_not_touch_original(self):
        moved = move_box(BOX, 50, -30, W, H)
        self.assertEqual((moved["x1"], moved["y1"], moved["x2"], moved["y2"]), (150.0, 170.0, 350.0, 370.0))
        self.assertEqual(moved["cls"], 2)
        self.assertEqual(BOX["x1"], 100.0)                         # 원본 dict 는 그대로

    def test_move_stops_at_image_edges(self):
        far = move_box(BOX, 5000, 5000, W, H)
        self.assertEqual((far["x2"], far["y2"]), (float(W), float(H)))
        self.assertEqual(far["x2"] - far["x1"], 200.0)             # 크기는 그대로
        near = move_box(BOX, -5000, -5000, W, H)
        self.assertEqual((near["x1"], near["y1"]), (0.0, 0.0))
        self.assertEqual(near["y2"] - near["y1"], 200.0)


class ResizeTest(unittest.TestCase):
    def test_each_handle_moves_only_its_edges(self):
        self.assertEqual(resize_box(BOX, "e", 350, 999, W, H)["x2"], 350)
        e = resize_box(BOX, "e", 350, 999, W, H)
        self.assertEqual((e["y1"], e["y2"]), (200.0, 400.0))       # e 는 가로만
        n = resize_box(BOX, "n", 0, 150, W, H)
        self.assertEqual((n["y1"], n["x1"], n["x2"]), (150, 100.0, 300.0))
        se = resize_box(BOX, "se", 320, 450, W, H)
        self.assertEqual((se["x1"], se["y1"], se["x2"], se["y2"]), (100.0, 200.0, 320, 450))
        nw = resize_box(BOX, "nw", 60, 120, W, H)
        self.assertEqual((nw["x1"], nw["y1"], nw["x2"], nw["y2"]), (60, 120, 300.0, 400.0))

    def test_cannot_cross_the_opposite_edge(self):
        r = resize_box(BOX, "e", 10, 300, W, H)                    # 오른쪽 변을 왼쪽 변 너머로 끌기
        self.assertEqual(r["x2"] - r["x1"], MIN_BOX_PX)
        r = resize_box(BOX, "n", 0, 900, W, H)
        self.assertEqual(r["y2"] - r["y1"], MIN_BOX_PX)

    def test_stays_inside_the_image(self):
        r = resize_box(BOX, "se", 5000, 5000, W, H)
        self.assertEqual((r["x2"], r["y2"]), (float(W), float(H)))
        r = resize_box(BOX, "nw", -50, -50, W, H)
        self.assertEqual((r["x1"], r["y1"]), (0, 0))

    def test_small_box_at_the_edge_can_grow_inward(self):
        edge = {"cls": 1, "x1": 997.0, "y1": 100.0, "x2": 1000.0, "y2": 200.0}     # 폭 3px, 오른쪽 가장자리
        r = resize_box(edge, "w", 999, 150, W, H)
        self.assertLessEqual(r["x2"], W)
        self.assertGreaterEqual(r["x2"] - r["x1"], MIN_BOX_PX)

    def test_original_is_never_modified(self):
        before = dict(BOX)
        resize_box(BOX, "sw", 10, 10, W, H)
        self.assertEqual(BOX, before)


if __name__ == "__main__":
    unittest.main()
