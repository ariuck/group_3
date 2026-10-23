"""Acceptance checker regression tests using synthetic files only."""
import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("acceptance_check", ROOT / "scripts/qa_acceptance_check.py")
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class CheckUseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "subject8"
        self.root.mkdir()
        self.root_patch = patch.object(qa, "PROJECT_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        qa.rows.clear()
        for name in ("scripts/08_predict_images.py", "src/inference.py"):
            self.write(name, "# synthetic fixture")

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def gui(self):
        self.write("app/static/app.js", "function saveTxt() { /* toFixed(6) new Blob a.download */ }")
        self.write("app/static/index.html", "<button>라벨 후보 저장</button>")

    def status(self, item):
        return next(row[2] for row in qa.rows if row[1] == item)

    def test_gui_export_does_not_require_the_unshipped_batch_tool(self):
        self.gui()
        qa.check_use()
        self.assertEqual(self.status("웹 GUI의 YOLO TXT 후보 저장 구현이 있다"), "PASS")
        self.assertEqual(self.status("전용 Auto Label 배치 도구"), "NOT_DELIVERED")
        self.assertEqual(self.status("후보 TXT → 교과 7 수정·승인 전체 흐름"), "MANUAL")

    def test_absent_gui_is_a_failure_even_when_batch_file_exists(self):
        self.write("scripts/12_auto_label.py", "# only a fixture")
        qa.check_use()
        self.assertEqual(self.status("웹 GUI의 YOLO TXT 후보 저장 구현이 있다"), "FAIL")

    def test_current_videos_are_found_without_populating_legacy_demo_folders(self):
        self.gui()
        videos = self.root / "presentation/private/videos"
        videos.mkdir(parents=True)
        (videos / "one.mp4").write_bytes(b"synthetic video fixture")
        (videos / "two.webm").write_bytes(b"synthetic video fixture")
        qa.check_use()
        self.assertEqual(self.status("발표용 녹화 시연 영상의 로컬 준비"), "PASS")
        self.assertEqual(self.status("초기 demo/ 폴더는 현행 발표 준비의 필수 경로가 아님"), "INFO")

    def test_zero_byte_video_is_not_accepted_as_prepared_media(self):
        self.gui()
        videos = self.root / "presentation/private/videos"
        videos.mkdir(parents=True)
        (videos / "one.mp4").write_bytes(b"fixture")
        (videos / "empty.mp4").touch()
        qa.check_use()
        self.assertEqual(self.status("발표용 녹화 시연 영상의 로컬 준비"), "MANUAL")

    def test_output_override_preserves_default_and_main_clears_old_rows(self):
        target = self.root / "custom.csv"
        default = self.root / "default.csv"
        default.write_text("keep original", encoding="utf-8")
        def only_info():
            qa.add("fixture", "reference only", "INFO", "synthetic")
        names = ("check_dataset", "check_model", "check_evaluation", "check_use", "check_env")
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(qa, "OUT_CSV", default))
            for name in names:
                stack.enter_context(patch.object(qa, name, only_info))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(qa.main(["--output", str(target)]), 0)
                self.assertEqual(qa.main(["--output", str(target)]), 0)
        with target.open(encoding="utf-8-sig", newline="") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 5)
        self.assertEqual(default.read_text(encoding="utf-8"), "keep original")


if __name__ == "__main__":
    unittest.main()
