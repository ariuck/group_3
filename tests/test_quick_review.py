"""한 키 검수(Enter=이상 없음 · R=수정 필요 · N=미작업으로) · 저장 안 됨 표시 · 작업 진행 요약 시험.

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_quick_review.py
"""
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.manifest import manifest_writer as mf

STATUSES = {"a0": "수정 완료", "a1": "검수 완료", "a2": "수정 필요"}        # a3~a5 는 아직 기록이 없다


class Ev:
    def __init__(self, x, y, state=0):
        self.x, self.y, self.state = x, y, state


def make_app():
    from src.ui import main_window as mw
    tmp = Path(tempfile.mkdtemp())
    ds = tmp / "raw" / "DS1"
    (ds / "images" / "train").mkdir(parents=True)
    (ds / "labels" / "train").mkdir(parents=True)
    for i in range(6):
        Image.new("RGB", (800, 500), "green").save(ds / "images" / "train" / f"a{i}.jpg")
    (ds / "labels" / "train" / "a3.txt").write_text("2 0.5 0.5 0.2 0.2\n")
    settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = tmp / "raw", tmp / "work", tmp / "m.csv"
    rows = []
    for stem, status in STATUSES.items():
        r = {h: "" for h in mf.HEADERS}
        r.update({"이미지 파일명": f"{stem}.jpg", "상태": status, "출처 데이터셋": "DS1", "원래 split": "train"})
        rows.append(r)
    mf._save(settings.MANIFEST_PATH, rows)
    infos = []
    mw.messagebox.showwarning = mw.messagebox.showerror = lambda *a, **k: None
    mw.messagebox.showinfo = lambda *a, **k: infos.append(a)
    mw.messagebox.askyesnocancel = lambda *a, **k: False
    root = mw.make_root()
    app = mw.Day1Labeler(root)
    root.geometry("1300x850")
    root.update()
    app.on_drop([str(ds)])
    root.update()
    return root, app, tmp, infos


class QuickReviewTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root, self.app, tmp, self.infos = make_app()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.app.require_scene_type = False          # 이 시험들은 한 키 검수 흐름 자체를 본다 (이미지 유형 확인은 아래 SceneTypeTest 에서)

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def settle(self):
        for _ in range(200):
            self.root.update()
            if self.app._nav_pending is None and self.app._nav_job is None:
                break

    def status_in_manifest(self, name):
        rows = mf._load(Path(settings.MANIFEST_PATH))
        hit = [r for r in rows if r["이미지 파일명"] == name]
        return (hit[0]["상태"], hit[0]["발견된 문제"]) if hit else None

    def go_to(self, name):
        self.app.move_to(next(p for p in self.app.navigator.files if p.name == name))
        self.settle()

    # ── Enter: 이상 없음 ─────────────────────────────────────────
    def test_enter_marks_done_saves_and_moves_on(self):
        self.go_to("a3.jpg")
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.status_in_manifest("a3.jpg")[0], "검수 완료")
        self.assertEqual(self.app.image_path.name, "a4.jpg")
        self.assertFalse(self.app.dirty)

    def test_enter_after_editing_is_recorded_as_edited(self):
        self.go_to("a3.jpg")
        self.app.history.push(self.app.boxes)
        self.app.boxes[0]["x1"] += 40
        self.app.mark_changed()
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.status_in_manifest("a3.jpg")[0], "수정 완료")            # 고쳤으면 '수정 완료' (고친 사진이라는 정보를 지키기 위해)

    def test_reviewer_name_follows_to_the_next_photos_but_never_replaces_a_written_one(self):
        """검수자 이름을 한 번 쓰면 다음 사진의 빈 칸에 미리 채워지고, 이미 이름이 있는 사진은 그대로 둔다"""
        self.go_to("a3.jpg")
        self.app.form._vars["검수자"].set("손상우")                         # 사람이 직접 씀
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a4.jpg")
        self.assertEqual(self.app.form.get_values()["검수자"], "손상우")    # 다음 사진(빈 칸)에 미리 채워짐
        self.assertFalse(self.app.dirty)                                  # 채운 것만으로는 '저장 안 됨' 이 아니다
        self.assertEqual(self.app._load_state, None)
        # 이름이 이미 적힌 사진: 그대로
        rows = mf._load(Path(settings.MANIFEST_PATH))
        for r in rows:
            if r["이미지 파일명"] == "a1.jpg":
                r["검수자"] = "지혜성"
        mf._save(Path(settings.MANIFEST_PATH), rows)
        self.go_to("a1.jpg")
        self.assertEqual(self.app.form.get_values()["검수자"], "지혜성")
        # 저장하면 미리 채운 이름이 검수표에 기록된다
        self.go_to("a4.jpg")
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual([r["검수자"] for r in mf._load(Path(settings.MANIFEST_PATH)) if r["이미지 파일명"] == "a4.jpg"], ["손상우"])
        self.assertEqual([r["검수자"] for r in mf._load(Path(settings.MANIFEST_PATH)) if r["이미지 파일명"] == "a1.jpg"], ["지혜성"])

    def test_enter_on_the_last_photo_saves_and_stays(self):
        self.go_to("a5.jpg")
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.status_in_manifest("a5.jpg")[0], "검수 완료")
        self.assertEqual(self.app.image_path.name, "a5.jpg")

    def test_enter_does_nothing_without_a_photo(self):
        self.app.pil_image = None
        self.app.mark_ok_and_next()                                                   # 오류 없이 무시
        self.assertIsNone(self.status_in_manifest("a3.jpg"))

    # ── R: 수정 필요 ─────────────────────────────────────────────
    def test_r_marks_review_and_prepares_the_reason(self):
        self.go_to("a4.jpg")
        self.app.mark_review()
        v = self.app.form.get_values()
        self.assertEqual(v["상태"], "수정 필요")
        self.assertEqual(v["발견된 문제"], "REVIEW:")                                 # 이유를 이어서 쓰도록 미리 채움
        self.assertTrue(self.app.dirty)
        self.assertIsNone(self.status_in_manifest("a4.jpg"))                          # 아직 저장 전

    def test_r_keeps_a_reason_that_was_already_written(self):
        self.go_to("a4.jpg")
        self.app.form.set_values({"발견된 문제": "REVIEW: class_ambiguous"})
        self.app.mark_review()
        self.assertEqual(self.app.form.get_values()["발견된 문제"], "REVIEW: class_ambiguous")

    def test_enter_in_the_reason_box_saves_and_moves_on(self):
        self.go_to("a4.jpg")
        self.app.mark_review()
        self.app.form.set_values({**self.app.form.get_values(), "발견된 문제": "REVIEW: tiny_object"})
        self.app.form._submit(None)                                                   # 이유 칸에서 Enter
        self.settle()
        self.assertEqual(self.status_in_manifest("a4.jpg"), ("수정 필요", "REVIEW: tiny_object"))
        self.assertEqual(self.app.image_path.name, "a5.jpg")

    def test_the_keys_are_bound(self):
        for key in ("<Return>", "r", "n"):
            self.assertTrue(self.root.bind(key), key)

    # ── N: 아직 안 한 사진으로 ──────────────────────────────────
    def test_n_jumps_to_the_next_unworked_photo(self):
        self.go_to("a0.jpg")
        self.app.go_next_unworked()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a3.jpg")                          # a1·a2 는 이미 기록이 있다
        self.app.go_next_unworked()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a4.jpg")

    def test_n_wraps_around_to_the_beginning(self):
        for name in ("a0", "a1", "a2"):                                               # 앞쪽 사진을 모두 '미작업'으로 만든다
            pass
        mf._save(settings.MANIFEST_PATH, [r for r in mf._load(Path(settings.MANIFEST_PATH)) if r["이미지 파일명"] != "a1.jpg"])
        self.go_to("a5.jpg")
        self.app.go_next_unworked()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a1.jpg")                          # 끝까지 없으면 처음부터 다시 찾는다

    def test_n_when_everything_is_worked(self):
        for name in ("a3", "a4", "a5"):
            self.go_to(f"{name}.jpg")
            self.app.save()
        self.go_to("a0.jpg")
        self.infos.clear()
        self.app.go_next_unworked()
        self.assertEqual(self.app.image_path.name, "a0.jpg")
        self.assertIn("작업하지 않은 사진이 없습니다", self.app.status.cget("text"))

    # ── 상태줄: 결과 메시지가 마우스 좌표 안내에 덮이지 않는다 ───────
    def hover(self):
        e = Ev(self.app.canvas.winfo_width() // 2, self.app.canvas.winfo_height() // 2)
        self.app.on_mouse_move(e)

    def test_save_result_survives_moving_the_mouse(self):
        """(수정한 문제) 저장 결과 메시지가 마우스를 움직이자마자 좌표 안내로 사라지던 문제"""
        self.go_to("a3.jpg")
        self.app.save()
        message = self.app.status.cget("text")
        self.assertIn("저장 완료", message)
        self.hover()
        self.assertEqual(self.app.status.cget("text"), message)

    def test_hover_help_appears_again_after_the_hold_time(self):
        self.go_to("a3.jpg")
        self.app.save()
        self.app._status_hold_until -= 10                       # 시간이 충분히 지났다고 본다
        self.hover()
        self.assertIn("원본 좌표", self.app.status.cget("text"))

    def test_hover_help_keeps_updating_while_nothing_else_was_said(self):
        self.go_to("a3.jpg")
        self.app._status_hold_until = 0.0
        self.hover()
        first = self.app.status.cget("text")
        self.assertIn("원본 좌표", first)
        self.app.on_mouse_move(Ev(self.app.canvas.winfo_width() // 2 + 7, self.app.canvas.winfo_height() // 2 + 3))
        self.assertNotEqual(self.app.status.cget("text"), first)  # 좌표가 따라 바뀐다

    def test_a_new_message_always_replaces_the_old_one(self):
        self.app.set_status("첫 번째")
        self.app.set_status("두 번째")
        self.assertEqual(self.app.status.cget("text"), "두 번째")

    # ── 저장 안 됨 표시 · 작업 진행 요약 ─────────────────────────
    def test_unsaved_badge_follows_the_changes(self):
        self.go_to("a3.jpg")
        self.assertEqual(self.app.dirty_label.cget("text"), "")
        self.app.history.push(self.app.boxes)
        self.app.boxes[0]["x1"] += 30
        self.app.mark_changed()
        self.assertIn("저장 안 됨", self.app.dirty_label.cget("text"))
        self.app.save()
        self.assertEqual(self.app.dirty_label.cget("text"), "")

    def test_progress_summary(self):
        self.assertEqual(self.app.strip.summary.cget("text"), "작업 3/6 (50%)  ·  검수 완료 1  ·  수정 완료 1  ·  수정 필요 1")
        self.go_to("a4.jpg")
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.app.strip.summary.cget("text"), "작업 4/6 (67%)  ·  검수 완료 2  ·  수정 완료 1  ·  수정 필요 1")

    def test_summary_is_empty_without_photos(self):
        self.app.navigator.all_files = []
        self.app.update_summary()
        self.assertEqual(self.app.strip.summary.cget("text"), "")


class SceneTypeTest(unittest.TestCase):
    """Enter 로 넘어가려면 이미지 유형을 골라야 한다"""

    def setUp(self):
        try:
            self.root, self.app, tmp, self.infos = make_app()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.assertTrue(self.app.require_scene_type)                       # 기본은 '켜짐'

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def settle(self):
        for _ in range(200):
            self.root.update()
            if self.app._nav_pending is None and self.app._nav_job is None:
                break

    def go_to(self, name):
        self.app.move_to(next(p for p in self.app.navigator.files if p.name == name))
        self.settle()

    def manifest_row(self, name):
        hit = [r for r in mf._load(Path(settings.MANIFEST_PATH)) if r["이미지 파일명"] == name]
        return hit[0] if hit else None

    # ── 이미지 유형 ────────────────────────────────────────────────
    def test_enter_does_not_move_on_while_the_image_type_is_blank(self):
        self.go_to("a3.jpg")
        self.assertEqual(self.app.form.get_values()["이미지 유형"], "")
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a3.jpg")              # 그대로 머문다
        self.assertIsNone(self.manifest_row("a3.jpg"))                    # 저장도 기록도 하지 않는다
        self.assertIn("이미지 유형을 먼저 골라", self.app.status.cget("text"))
        self.assertIn("Ctrl+1", self.app.status.cget("text"))
        chips = self.app.form._chips["이미지 유형"]
        self.assertGreater(int(str(chips.cget("highlightthickness"))), 0)   # 고를 곳이 깜빡인다
        self.root.update()

    def test_after_choosing_the_type_enter_works_and_it_is_recorded(self):
        self.go_to("a3.jpg")
        self.app.choose_scene(1)                                          # Ctrl+2 = 정상 김치
        self.assertEqual(self.app.form.get_values()["이미지 유형"], "정상 김치")
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a4.jpg")
        self.assertEqual(self.manifest_row("a3.jpg")["이미지 유형"], "정상 김치")

    def test_keys_ctrl_1_to_4_choose_the_four_types(self):
        self.go_to("a3.jpg")
        names = ["김치+대상 객체", "정상 김치", "대상 객체 단독", "판단 어려움"]
        for i, name in enumerate(names, 1):
            self.root.event_generate(f"<Control-Key-{i}>")
            self.root.update()
            self.assertEqual(self.app.form.get_values()["이미지 유형"], name)

    def test_the_review_enter_in_the_text_cells_is_checked_too(self):
        self.go_to("a4.jpg")
        self.app.mark_review()                                            # R: 수정 필요 + 이유 쓰기
        self.app.on_form_submit()                                         # 이유 칸에서 Enter
        self.settle()
        self.assertEqual(self.app.image_path.name, "a4.jpg")              # 이미지 유형을 안 골랐으므로 머문다
        self.app.choose_scene(3)                                          # 판단 어려움
        self.app.on_form_submit()
        self.settle()
        self.assertEqual(self.app.image_path.name, "a5.jpg")
        self.assertEqual(self.manifest_row("a4.jpg")["상태"], "수정 필요")

    def test_w_and_ctrl_s_are_not_blocked(self):
        self.go_to("a3.jpg")
        self.app.save_and_next()                                          # W = 작업 중 저장은 막지 않는다
        self.settle()
        self.assertEqual(self.app.image_path.name, "a4.jpg")
        self.assertIsNotNone(self.manifest_row("a3.jpg"))

    def test_already_chosen_type_is_kept_and_no_photo_means_no_error(self):
        self.go_to("a3.jpg")
        self.app.choose_scene(0)
        self.app.mark_ok_and_next()
        self.settle()
        self.assertEqual(self.manifest_row("a3.jpg")["이미지 유형"], "김치+대상 객체")
        self.app.pil_image = None
        self.app.choose_scene(1)                                          # 사진이 없으면 아무 일도 없다
        self.app.mark_ok_and_next()
        self.app.on_form_submit()

    def test_shutdown_leaves_no_pending_flash(self):
        self.go_to("a3.jpg")
        self.app.mark_ok_and_next()                                       # 깜빡임이 예약된다
        self.app.shutdown()
        self.assertEqual(len(self.root.tk.splitlist(self.root.tk.call("after", "info"))), 0)



if __name__ == "__main__":
    unittest.main()
