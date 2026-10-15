"""상태별 보기 필터 화면 시험 (사진 6장 + 검수표 몇 줄).

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_filter_ui.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.manifest import manifest_writer as mw_

STATUSES = {"a0": "수정 완료", "a1": "검수 완료", "a2": "수정 필요"}       # a3~a5 는 검수표에 기록이 없다 = 미작업


def make_app():
    from src.ui import main_window as mw
    tmp = Path(tempfile.mkdtemp())
    ds = tmp / "raw" / "DS1"
    (ds / "images" / "train").mkdir(parents=True)
    (ds / "labels" / "train").mkdir(parents=True)
    for i in range(6):
        Image.new("RGB", (800, 500), "green").save(ds / "images" / "train" / f"a{i}.jpg")
    settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = tmp / "raw", tmp / "work", tmp / "m.csv"
    rows = []
    for stem, status in STATUSES.items():
        r = {h: "" for h in mw_.HEADERS}
        r.update({"이미지 파일명": f"{stem}.jpg", "상태": status, "출처 데이터셋": "DS1", "원래 split": "train"})
        rows.append(r)
    mw_._save(settings.MANIFEST_PATH, rows)
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


class FilterUiTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root, self.app, tmp, self.infos = make_app()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.addCleanup(shutil.rmtree, tmp, True)

    def tearDown(self):
        for job in (self.app._resize_job, self.app._render_job, self.app._nav_job):
            if job is not None:
                self.root.after_cancel(job)
        self.app.strip.stop()
        self.root.destroy()

    def choose(self, name):
        self.app.filter_var.set(name)
        self.app.on_filter_changed()
        self.root.update()

    def names(self):
        return [p.stem for p in self.app.navigator.files]

    def test_starts_with_everything(self):
        self.assertEqual(self.app.filter_var.get(), "전체")
        self.assertEqual(len(self.names()), 6)
        self.assertEqual(self.app.navigator.index, 0)

    def test_filter_by_status_goes_to_the_first_match(self):
        self.choose("수정 필요")
        self.assertEqual(self.names(), ["a2"])
        self.assertEqual(self.app.image_path.stem, "a2")                 # 지금 사진(a0)이 걸러졌으니 첫 사진으로
        self.assertEqual(self.app.nav_text(), "1 / 1")
        self.assertIn("1개 / 전체 6개", self.app.strip.title.cget("text"))
        self.assertEqual([p.stem for p in self.app.strip.files], ["a2"])

    def test_not_worked_yet_means_not_in_the_manifest(self):
        self.choose("미작업 (기록 없음)")
        self.assertEqual(self.names(), ["a3", "a4", "a5"])

    def test_current_photo_stays_when_it_matches(self):
        self.app.move_to(self.app.navigator.files[1])                    # a1 (검수 완료)
        loads = []
        real = self.app.load_image
        self.app.load_image = lambda p: (loads.append(p), real(p))[1]
        self.choose("검수 완료")
        self.assertEqual(self.names(), ["a1"])
        self.assertEqual(self.app.image_path.stem, "a1")
        self.assertEqual(loads, [])                                      # 같은 사진을 다시 읽지 않는다

    def test_next_and_previous_follow_the_filtered_list(self):
        self.choose("미작업 (기록 없음)")
        self.assertEqual(self.app.image_path.stem, "a3")
        self.app.go_next(); self.app.go_next()
        for _ in range(100):
            self.root.update()
            if self.app._nav_pending is None:
                break
        self.assertEqual(self.app.image_path.stem, "a5")
        self.assertEqual(self.app.nav_text(), "3 / 3")
        self.app.go_next()
        self.root.update()
        self.assertEqual(self.app.image_path.stem, "a5")                 # 끝에서 더 못 간다 (a0 으로 돌아가지 않는다)

    def test_no_match_shows_a_message_and_goes_back_to_everything(self):
        self.choose("제외")
        self.assertEqual(len(self.names()), 6)
        self.assertEqual(self.app.filter_var.get(), "전체")
        self.assertTrue(self.infos)                                      # '해당하는 사진이 없습니다' 안내

    def test_empty_result_restores_the_number_display(self):
        """(수정한 버그) 걸러서 본 뒤 해당 사진이 없는 필터를 고르면 위쪽 번호·총 개수가 이전 값으로 남던 문제"""
        self.choose("수정 필요")
        self.assertEqual(self.app.nav_text(), "1 / 1")
        self.choose("제외")                                              # 해당하는 사진이 없다 → 전체로 되돌림
        self.assertEqual(len(self.names()), 6)
        self.assertEqual(self.app.nav_text(), "3 / 6")                   # 보던 사진(a2)의 번호와 전체 개수
        self.assertEqual(str(self.app.btn_next.cget("state")), "normal")

    def test_cancelled_filter_restores_the_number_display(self):
        from src.ui import main_window as mw
        self.choose("수정 필요")                                         # a2 한 장만 보임
        mw.messagebox.askyesnocancel = lambda *a, **k: None
        self.app.dirty = True
        self.choose("검수 완료")                                         # 지금 사진(a2)이 걸러져 이동해야 하는데 취소
        self.assertEqual(self.app.filter_var.get(), "전체")
        self.assertEqual(self.app.nav_text(), "3 / 6")

    def test_back_to_everything(self):
        self.choose("수정 필요")
        self.choose("전체")
        self.assertEqual(len(self.names()), 6)
        self.assertEqual(self.app.image_path.stem, "a2")                 # 보던 사진은 그대로
        self.assertEqual(self.app.navigator.index, 2)
        self.assertNotIn("전체", self.app.strip.title.cget("text").replace("이미지 목록", ""))

    def test_opening_a_hidden_photo_clears_the_filter_display(self):
        self.choose("수정 필요")
        hidden = self.app.navigator.all_files[0]                         # a0 은 필터에 걸러진 사진
        self.app.load_image(hidden)
        self.root.update()
        self.assertEqual(self.app.filter_var.get(), "전체")
        self.assertEqual(len(self.names()), 6)

    def test_unsaved_change_cancel_keeps_everything(self):
        from src.ui import main_window as mw
        mw.messagebox.askyesnocancel = lambda *a, **k: None             # 저장 확인에서 '취소'
        self.app.dirty = True
        self.choose("수정 필요")                                         # 지금 사진(a0)이 걸러지므로 이동이 필요 → 취소
        self.assertEqual(self.app.image_path.stem, "a0")
        self.assertEqual(self.app.filter_var.get(), "전체")
        self.assertEqual(len(self.names()), 6)

    def test_filter_with_nothing_open_is_ignored(self):
        self.app.pil_image = None
        self.choose("수정 필요")
        self.assertEqual(self.app.filter_var.get(), "전체")


if __name__ == "__main__":
    unittest.main()
