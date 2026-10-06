"""방향키를 누르고 있을 때(반복 입력) 사진을 입력마다 읽지 않고 쌓이지 않는지 확인한다.

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_step_hold.py
"""
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image

from src import settings


def make_app(count):
    from src.ui import main_window as mw
    tmp = Path(tempfile.mkdtemp())
    ds = tmp / "raw" / "DS1"
    (ds / "images" / "train").mkdir(parents=True)
    (ds / "labels" / "train").mkdir(parents=True)
    base = Image.effect_noise((1600, 1200), 80).convert("RGB")      # 압축이 잘 안 되는 큰 사진
    for i in range(count):
        base.save(ds / "images" / "train" / f"img{i:03d}.jpg", quality=90)
    settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = tmp / "raw", tmp / "work", tmp / "m.csv"
    mw.messagebox.showwarning = mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
    asked = []
    mw.messagebox.askyesnocancel = lambda *a, **k: (asked.append(1), False)[1]
    root = mw.make_root()
    app = mw.Day1Labeler(root)
    root.geometry("1200x800")
    root.update()
    app.on_drop([str(ds)])
    root.update()
    return root, app, asked, tmp


def drain(root, app):
    assert app.wait_for_nav(), "이동이 끝나지 않았다"
    root.update()


class StepHoldTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root, self.app, self.asked, tmp = make_app(60)
            self.addCleanup(shutil.rmtree, tmp, True)         # 시험이 만든 큰 가짜 사진을 시험이 끝나면 지운다
        except Exception as e:                       # 화면이 없는 환경이면 건너뛴다
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        loads = self.loads = []
        real = self.app.decode_image                              # 사진을 실제로 읽는 함수 (방향키 이동은 다른 스레드에서 이것을 부른다)
        self.app.decode_image = lambda p: (loads.append(Path(p).name), real(p))[1]

    def tearDown(self):
        for job in (self.app._resize_job, self.app._render_job, self.app._nav_job):   # 남은 예약 작업을 취소해야 종료 때 오류 메시지가 안 난다
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()

    def test_burst_of_keys_reads_only_the_destination(self):
        for _ in range(20):                          # 처리보다 빨리 20번 연속 입력 (키를 누르고 있는 상황)
            self.app.go_next()
        self.assertEqual(self.app.nav_text(), "21 / 60")   # 번호는 바로 바뀐다
        drain(self.root, self.app)
        self.assertEqual(self.loads, ["img020.jpg"])                  # 사진은 도착지 한 장만 읽는다
        self.assertEqual(self.app.image_path.name, "img020.jpg")
        self.assertEqual(self.app.nav_text(), "21 / 60")

    def test_backlog_does_not_keep_moving_after_release(self):
        gap = 20                                      # 사진 읽기(수십 ms)보다 빠른 입력
        for i in range(40):
            self.root.after(i * gap, self.app.go_next)
        start = time.perf_counter()
        while time.perf_counter() - start < 40 * gap / 1000 + 0.05:
            self.root.update()
        drain(self.root, self.app)
        self.assertEqual(self.app.image_path.name, "img040.jpg")      # 정확히 40장 뒤
        self.assertLess(len(self.loads), 40)                          # 입력마다 읽지 않았다

    def test_stops_at_both_ends(self):
        for _ in range(100):
            self.app.go_next()
        drain(self.root, self.app)
        self.assertEqual(self.app.nav_text(), "60 / 60")
        for _ in range(100):
            self.app.go_prev()
        drain(self.root, self.app)
        self.assertEqual(self.app.nav_text(), "1 / 60")

    def test_unsaved_change_asks_only_once_for_a_burst(self):
        self.app.dirty = True                         # 확인창에서 '저장 안 하고 이동'(False) 을 고른 경우
        for _ in range(5):
            self.app.go_next()
        drain(self.root, self.app)
        self.assertEqual(len(self.asked), 1)          # 연속 입력 동안 확인창은 한 번만
        self.assertEqual(self.app.nav_text(), "6 / 60")

    def test_cancel_in_the_confirm_dialog_stays(self):
        from src.ui import main_window as mw
        mw.messagebox.askyesnocancel = lambda *a, **k: (self.asked.append(1), None)[1]    # 취소
        self.app.dirty = True
        for _ in range(3):
            self.app.go_next()
        drain(self.root, self.app)
        self.assertEqual(self.app.nav_text(), "1 / 60")    # 이동하지 않는다


class JumpToNumberTest(unittest.TestCase):
    """사진 번호를 직접 입력해 이동 (혜성 제안)."""

    def setUp(self):
        try:
            self.root, self.app, self.asked, tmp = make_app(60)
            self.addCleanup(shutil.rmtree, tmp, True)         # 시험이 만든 큰 가짜 사진을 시험이 끝나면 지운다
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        from src.ui import main_window as mw
        self.warned = []
        mw.messagebox.showwarning = lambda *a, **k: self.warned.append(a[0])

    def tearDown(self):
        for job in (self.app._resize_job, self.app._render_job, self.app._nav_job):   # 남은 예약 작업을 취소해야 종료 때 오류 메시지가 안 난다
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()

    def jump(self, text):
        self.app.entry_index.delete(0, "end")
        self.app.entry_index.insert(0, text)
        self.app.jump_to_entered_index()
        self.root.update()

    def test_jump_to_number(self):
        self.assertEqual(self.app.nav_text(), "1 / 60")
        self.jump("37")
        self.assertEqual(self.app.image_path.name, "img036.jpg")
        self.assertEqual(self.app.nav_text(), "37 / 60")
        self.assertEqual(self.app.strip.current, 36)                       # 하단 사진 목록도 따라간다

    def test_out_of_range_and_garbage_are_rejected(self):
        for text in ("0", "61", "abc", "-3", "1.5"):
            self.jump(text)
            self.assertEqual(self.app.image_path.name, "img000.jpg", text)
            self.assertEqual(self.app.nav_text(), "1 / 60", text)        # 입력칸은 현재 번호로 되돌아간다
        self.assertEqual(len(self.warned), 5)

    def test_cancel_in_the_confirm_dialog_keeps_the_number(self):
        from src.ui import main_window as mw
        mw.messagebox.askyesnocancel = lambda *a, **k: None             # 취소
        self.app.dirty = True
        self.jump("10")
        self.assertEqual(self.app.nav_text(), "1 / 60")
        self.assertEqual(self.app.image_path.name, "img000.jpg")

    def test_arrow_keys_continue_from_the_jumped_photo(self):
        self.jump("30")
        self.app.go_next()
        drain(self.root, self.app)
        self.assertEqual(self.app.nav_text(), "31 / 60")


class AsyncNavTest(unittest.TestCase):
    """방향키로 넘길 때 사진 읽기는 다른 스레드에서 한다 — 읽는 동안에도 화면이 멈추지 않고, 편집 중인 내용은 지켜진다."""

    def setUp(self):
        try:
            self.root, self.app, self.asked, tmp = make_app(30)
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.real_decode = self.app.decode_image
        self.slow = 0.0
        self.broken = set()

        def decode(path):
            time.sleep(self.slow)
            if Path(path).name in self.broken:
                raise OSError("깨진 사진")
            return self.real_decode(path)
        self.app.decode_image = decode

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def test_the_screen_keeps_responding_while_a_photo_is_being_read(self):
        self.slow = 0.4
        t0 = time.perf_counter()
        self.app.go_next()
        self.root.update()
        self.assertLess(time.perf_counter() - t0, 0.2)               # 읽는 데 0.4초가 걸려도 go_next 는 바로 돌아온다
        self.assertEqual(self.app.nav_text(), "2 / 30")                # 번호는 이미 바뀌었고
        ticks = 0
        while self.app._load_state is not None and not self.app._load_state["done"]:
            self.root.update()                                       # 읽는 동안에도 화면 갱신이 계속 돈다
            ticks += 1
            time.sleep(0.005)
        self.assertGreater(ticks, 10)
        self.assertTrue(self.app.wait_for_nav())
        self.assertEqual(self.app.image_path.name, "img001.jpg")

    def test_photos_passed_on_the_way_are_shown_and_the_final_one_wins(self):
        self.slow = 0.05
        shown = []
        real_apply = self.app.apply_image
        self.app.apply_image = lambda path, img, keep_pending=False: (shown.append(Path(path).name), real_apply(path, img, keep_pending))[1]
        start = time.monotonic()
        while time.monotonic() - start < 0.5:                         # 0.5초 동안 계속 넘긴다
            self.app.go_next()
            self.root.update()
            time.sleep(0.01)
        self.assertTrue(self.app.wait_for_nav())
        self.assertGreater(len(shown), 1)                              # 지나가는 사진도 화면에 올라간다 (멈춰 보이지 않게)
        self.assertEqual(shown[-1], self.app.image_path.name)
        self.assertEqual(self.app.nav_text(), f"{self.app.navigator.index + 1} / 30")
        self.assertEqual(self.app.strip.current, self.app.navigator.index)   # 번호·목록·화면이 같은 사진을 가리킨다

    def test_editing_while_a_photo_is_loading_cancels_the_move_and_keeps_the_edit(self):
        """(안전장치) 읽는 동안 BBox 를 고쳤는데 새 사진이 덮어써서 편집이 사라지면 안 된다"""
        self.slow = 0.3
        self.app.go_next()
        self.root.update()
        self.app.boxes.append({"cls": 1, "x1": 10.0, "y1": 10.0, "x2": 90.0, "y2": 80.0})   # 읽는 중에 새 BBox 를 그림
        self.app.history.push(self.app.boxes[:-1])
        self.app.mark_changed()
        self.assertTrue(self.app.wait_for_nav())
        self.assertEqual(self.app.image_path.name, "img000.jpg")      # 이동하지 않았다
        self.assertEqual(len(self.app.boxes), 1)                       # 편집은 그대로
        self.assertTrue(self.app.dirty)
        self.assertIn("이동을 취소", self.app.status.cget("text"))
        self.assertEqual(self.app.nav_text(), "1 / 30")                # 번호 표시도 원래대로

    def test_choosing_to_discard_does_not_cancel_the_move(self):
        from src.ui import main_window as mw
        mw.messagebox.askyesnocancel = lambda *a, **k: False          # '저장 안 하고 이동'
        self.app.dirty = True
        self.app.go_next()
        self.assertTrue(self.app.wait_for_nav())
        self.assertEqual(self.app.image_path.name, "img001.jpg")      # 버리기로 했으면 정상적으로 이동

    def test_opening_another_photo_meanwhile_wins(self):
        self.slow = 0.3
        self.app.go_next()
        self.root.update()
        other = self.app.navigator.files[7]
        self.app.decode_image = self.real_decode                      # 직접 여는 쪽은 바로 읽는다
        self.app.load_image(other)
        self.assertTrue(self.app.wait_for_nav(3))
        time.sleep(0.5)
        for _ in range(20):
            self.root.update()
        self.assertEqual(self.app.image_path, other)                  # 낡은 읽기 결과가 뒤늦게 덮어쓰지 않는다
        self.assertEqual(self.app.nav_text(), "8 / 30")

    def test_a_broken_photo_on_the_way_is_skipped(self):
        self.broken = {"img003.jpg"}
        self.slow = 0.02
        for _ in range(5):
            self.app.go_next()
        self.assertTrue(self.app.wait_for_nav())
        self.assertEqual(self.app.image_path.name, "img005.jpg")      # 지나가는 사진이 깨져 있어도 목적지에 도착한다

    def test_a_broken_destination_shows_an_error_and_stays(self):
        from src.ui import main_window as mw
        shown = []
        mw.messagebox.showerror = lambda *a, **k: shown.append(a)
        self.broken = {"img001.jpg"}
        self.app.go_next()
        self.assertTrue(self.app.wait_for_nav())
        self.assertEqual(len(shown), 1)
        self.assertEqual(self.app.image_path.name, "img000.jpg")      # 지금 사진에 머문다
        self.assertEqual(self.app.nav_text(), "1 / 30")

    def test_closing_while_a_photo_is_loading_is_quiet(self):
        self.slow = 0.3
        self.app.go_next()
        self.root.update()
        self.app.shutdown()
        self.assertIsNone(self.app._load_state)
        self.assertEqual(len(self.root.tk.splitlist(self.root.tk.call("after", "info"))), 0)     # 남은 예약이 없다


if __name__ == "__main__":
    unittest.main()
