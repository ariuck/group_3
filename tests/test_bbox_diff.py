"""원본(RAW) 과 지금 BBox 비교 시험 (화면 없이).

실행 (프로젝트 폴더에서):  python -m unittest tests/test_bbox_diff.py
"""
import unittest

from src.bbox.bbox_diff import box_iou, diff_boxes, diff_summary


def B(cls, x1, y1, x2, y2):
    return {"cls": cls, "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


A = B(2, 100, 100, 200, 200)
C = B(5, 400, 300, 520, 380)


class IouTest(unittest.TestCase):
    def test_iou(self):
        self.assertEqual(box_iou(A, A), 1.0)
        self.assertEqual(box_iou(A, B(2, 300, 300, 400, 400)), 0.0)
        self.assertAlmostEqual(box_iou(A, B(2, 150, 100, 250, 200)), 1 / 3)      # 절반 겹침 → 5000 / 15000


class DiffTest(unittest.TestCase):
    def test_nothing_changed(self):
        r = diff_boxes([A, C], [dict(A), dict(C)])
        self.assertEqual(r, {"unchanged": [0, 1], "modified": [], "added": [], "deleted": []})

    def test_tiny_rounding_difference_is_still_unchanged(self):
        r = diff_boxes([A], [B(2, 100.2, 99.9, 200.3, 200.1)])
        self.assertEqual(r["unchanged"], [0])

    def test_added_and_deleted(self):
        r = diff_boxes([A, C], [dict(A), B(1, 700, 50, 760, 120)])
        self.assertEqual(r["unchanged"], [0])
        self.assertEqual(r["added"], [1])                          # 새로 그린 것
        self.assertEqual(r["deleted"], [1])                        # C 는 지워짐
        self.assertEqual(r["modified"], [])

    def test_moved_or_resized_is_modified(self):
        r = diff_boxes([A], [B(2, 110, 105, 215, 210)])
        self.assertEqual(r["modified"], [(0, 0)])
        self.assertEqual((r["added"], r["deleted"]), ([], []))

    def test_class_change_only_is_modified(self):
        r = diff_boxes([A], [B(6, 100, 100, 200, 200)])
        self.assertEqual(r["modified"], [(0, 0)])

    def test_far_move_counts_as_delete_plus_add(self):
        r = diff_boxes([A], [B(2, 600, 500, 700, 600)])            # 겹치지 않을 만큼 멀리
        self.assertEqual((r["added"], r["deleted"], r["modified"]), ([0], [0], []))

    def test_pairing_picks_the_best_overlap(self):
        raw = [B(2, 100, 100, 200, 200), B(2, 120, 100, 220, 200)]            # 서로 많이 겹치는 두 BBox
        cur = [B(2, 125, 100, 225, 200), B(2, 105, 100, 205, 200)]            # 순서를 바꿔 조금씩 옮김
        r = diff_boxes(raw, cur)
        self.assertEqual(r["modified"], [(1, 0), (0, 1)])
        self.assertEqual((r["added"], r["deleted"]), ([], []))

    def test_empty_lists(self):
        self.assertEqual(diff_boxes([], [])["unchanged"], [])
        r = diff_boxes([], [A])
        self.assertEqual(r["added"], [0])
        r = diff_boxes([A], [])
        self.assertEqual(r["deleted"], [0])

    def test_summary_text(self):
        r = diff_boxes([A, C], [dict(A), B(1, 700, 50, 760, 120)])
        self.assertEqual(diff_summary(r), "추가 1 · 수정 0 · 삭제 1 · 그대로 1")


if __name__ == "__main__":
    unittest.main()
