"""마지막 작업 위치 복원 시험.

저장·불러오기 함수는 화면 없이, 프로그램에서 이어서 열기는 화면(Tk)이 필요하다.
실행 (프로젝트 폴더에서):  python -m unittest tests/test_session.py
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.ui import session


class SessionFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.old = settings.WORK_DIR
        settings.WORK_DIR = self.tmp / "work"
        self.addCleanup(lambda: setattr(settings, "WORK_DIR", self.old))
        self.folder = self.tmp / "photos"
        self.folder.mkdir()
        self.image = self.folder / "a.jpg"
        Image.new("RGB", (10, 10)).save(self.image)

    def test_round_trip(self):
        self.assertTrue(session.save_session(self.folder, self.image))
        self.assertEqual(session.load_session(), (self.folder, self.image))

    def test_no_file_means_nothing_to_restore(self):
        self.assertIsNone(session.load_session())

    def test_missing_paths_are_ignored(self):
        session.save_session(self.folder, self.image)
        self.image.unlink()
        self.assertIsNone(session.load_session())                       # 사진이 사라졌다
        Image.new("RGB", (10, 10)).save(self.image)
        shutil.rmtree(self.folder)
        self.assertIsNone(session.load_session())                       # 폴더가 사라졌다

    def test_broken_file_is_ignored(self):
        session.session_path().parent.mkdir(parents=True)
        for text in ("not json", "{}", '{"folder": 1, "image": 2}', "[]"):
            session.session_path().write_text(text, encoding="utf-8")
            self.assertIsNone(session.load_session(), text)

    def test_nothing_is_saved_without_a_photo(self):
        self.assertFalse(session.save_session(None, None))
        self.assertFalse(session.session_path().exists())

    def test_only_two_paths_are_stored_and_no_temp_file_is_left(self):
        session.save_session(self.folder, self.image)
        data = json.loads(session.session_path().read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"folder", "image"})
        self.assertEqual([p.name for p in session.session_path().parent.iterdir()], ["_session.json"])


class RestoreInAppTest(unittest.TestCase):
    def setUp(self):
        from src.ui import main_window as mw
        self.mw = mw
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        ds = self.tmp / "raw" / "DS1"
        (ds / "images" / "train").mkdir(parents=True)
        (ds / "labels" / "train").mkdir(parents=True)
        for i in range(6):
            Image.new("RGB", (400, 300), "green").save(ds / "images" / "train" / f"a{i}.jpg")
        self.ds = ds
        settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = self.tmp / "raw", self.tmp / "work", self.tmp / "m.csv"
        mw.messagebox.showwarning = mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
        self.roots = []

    def tearDown(self):
        for root in self.roots:
            try:
                root.destroy()
            except Exception:  # noqa: BLE001
                pass

    def new_app(self):
        try:
            root = self.mw.make_root()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.roots.append(root)
        app = self.mw.Day1Labeler(root)
        root.update()
        return root, app

    def test_next_launch_continues_where_you_left(self):
        root, app = self.new_app()
        app.on_drop([str(self.ds)])
        app.load_image(app.navigator.files[3])
        root.update()
        root.destroy()                                                   # 프로그램을 끈다
        root2, app2 = self.new_app()                                     # 다시 켠다
        self.assertTrue(app2.restore_session())
        self.assertEqual(app2.image_path.name, "a3.jpg")
        self.assertEqual(app2.nav_text(), "4 / 6")                       # 폴더 전체 목록과 위치까지 복원
        self.assertEqual(app2.strip.current, 3)
        self.assertIn("이어서", app2.status.cget("text"))

    def test_returning_to_the_window_cleans_zone_markers(self):
        """탐색기에서 복사하고 창으로 돌아오면 표시 파일이 정리된다 (켜져 있는 동안에도)"""
        from types import SimpleNamespace
        root, app = self.new_app()
        d = settings.WORK_DIR / "DS1" / "labels" / "train"
        d.mkdir(parents=True)
        (d / "a0.txt").write_text("2 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        marker = d / "a0.txtZone.Identifier"
        marker.write_text("[ZoneTransfer]\nZoneId=3\n")
        app._zone_clean_t = 0.0
        app.on_window_focus(SimpleNamespace(widget=app.canvas))             # 안쪽 위젯의 포커스는 무시한다
        self.assertTrue(marker.exists())
        app.on_window_focus(SimpleNamespace(widget=root))
        self.assertFalse(marker.exists())
        self.assertTrue((d / "a0.txt").exists())                           # 라벨은 그대로
        self.assertIn("1개", app.status.cget("text"))
        marker.write_text("x")
        app.on_window_focus(SimpleNamespace(widget=root))                   # 2초 안에 다시 와도 매번 정리하지 않는다
        self.assertTrue(marker.exists())

    def test_shutdown_cancels_the_pending_restore(self):
        """(수정한 버그) 켜자마자 닫으면 예약된 복원 작업이 닫힌 창을 찾아 오류를 내던 문제"""
        root, app = self.new_app()
        self.assertIsNotNone(app._restore_job)
        app.shutdown()
        self.assertIsNone(app._restore_job)
        self.assertNotIn(str(app._restore_job), root.tk.call("after", "info"))
        self.assertEqual(len(root.tk.splitlist(root.tk.call("after", "info"))), 0)     # 남은 예약이 없다

    def test_fresh_start_without_a_record_does_nothing(self):
        root, app = self.new_app()
        self.assertFalse(app.restore_session())
        self.assertIsNone(app.pil_image)

    def test_does_not_override_something_you_already_opened(self):
        root, app = self.new_app()
        app.on_drop([str(self.ds)])
        app.load_image(app.navigator.files[2])
        root.destroy()
        root2, app2 = self.new_app()
        app2.load_image(app2.navigator.files[0] if app2.navigator.files else self.ds / "images" / "train" / "a0.jpg")
        self.assertFalse(app2.restore_session())                         # 이미 열린 사진이 있으면 건드리지 않는다
        self.assertEqual(app2.image_path.name, "a0.jpg")

    def test_deleted_photo_is_skipped_quietly(self):
        root, app = self.new_app()
        app.on_drop([str(self.ds)])
        app.load_image(app.navigator.files[4])
        root.destroy()
        (self.ds / "images" / "train" / "a4.jpg").unlink()
        root2, app2 = self.new_app()
        self.assertFalse(app2.restore_session())
        self.assertIsNone(app2.pil_image)


if __name__ == "__main__":
    unittest.main()
