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
    while app._nav_pending is not None or app._nav_job is not None:
        root.update()
    root.update()


class StepHoldTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root, self.app, self.asked, tmp = make_app(60)
            self.addCleanup(shutil.rmtree, tmp, True)         # 시험이 만든 큰 가짜 사진을 시험이 끝나면 지운다
        except Exception as e:                       # 화면이 없는 환경이면 건너뛴다
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        loads = self.loads = []
        real = self.app.load_image
        self.app.load_image = lambda p: (loads.append(Path(p).name), real(p))[1]

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


if __name__ == "__main__":
    unittest.main()
