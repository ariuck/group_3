"""말풍선(Tooltip)과 단축키 도움말(F1) 시험.

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_tooltip_help.py
"""
import shutil
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.ui import theme
from src.ui.help_dialog import SHORTCUT_GROUPS, all_bindings, show_shortcuts
from src.ui.tooltip import Tooltip


class TooltipTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        theme.setup(self.root)
        self.btn = tk.Button(self.root, text="x")
        self.btn.pack()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_shows_after_the_delay_and_hides_on_leave(self):
        tip = Tooltip(self.btn, "설명입니다", delay=20)
        self.btn.event_generate("<Enter>")
        self.assertIsNone(tip._tip)                                   # 바로 뜨지는 않는다
        for _ in range(40):
            self.root.update()
            if tip._tip is not None:
                break
            self.root.after(10)
        tip.show() if tip._tip is None else None
        self.assertIsNotNone(tip._tip)
        self.assertEqual([w.cget("text") for w in tip._tip.winfo_children()], ["설명입니다"])
        self.btn.event_generate("<Leave>")
        self.assertIsNone(tip._tip)

    def test_click_hides_it_and_a_quick_pass_never_shows_it(self):
        tip = Tooltip(self.btn, "설명", delay=30)
        tip.show()
        self.assertIsNotNone(tip._tip)
        self.btn.event_generate("<ButtonPress-1>")
        self.assertIsNone(tip._tip)
        self.btn.event_generate("<Enter>")
        self.btn.event_generate("<Leave>")                            # 지나가기만 하면 예약이 취소된다
        self.assertIsNone(tip._job)
        self.assertIsNone(tip._tip)

    def test_text_can_be_a_function_and_empty_text_shows_nothing(self):
        calls = []
        tip = Tooltip(self.btn, lambda: (calls.append(1), "동적 설명")[1])
        tip.show()
        self.assertEqual([w.cget("text") for w in tip._tip.winfo_children()], ["동적 설명"])
        tip._hide()
        empty = Tooltip(self.btn, "")
        empty.show()
        self.assertIsNone(empty._tip)

    def test_showing_twice_does_not_stack_windows(self):
        tip = Tooltip(self.btn, "설명")
        tip.show()
        first = tip._tip
        tip.show()
        self.assertIs(tip._tip, first)
        tip._hide()


class HelpDialogTest(unittest.TestCase):
    def setUp(self):
        from src.ui import main_window as mw
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        ds = self.tmp / "raw" / "DS1"
        (ds / "images" / "train").mkdir(parents=True)
        (ds / "labels" / "train").mkdir(parents=True)
        Image.new("RGB", (300, 200)).save(ds / "images" / "train" / "a.jpg")
        settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = self.tmp / "raw", self.tmp / "work", self.tmp / "m.csv"
        mw.messagebox.showwarning = mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
        try:
            self.root = mw.make_root()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.app = mw.Day1Labeler(self.root)
        self.root.update()

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def test_every_key_listed_in_the_help_is_really_bound(self):
        """도움말에 적힌 단축키가 실제로 연결되어 있는지 — 코드를 바꾸고 도움말을 안 고치면 여기서 잡힌다"""
        missing = [seq for seq in all_bindings() if not self.root.bind(seq)]
        self.assertEqual(missing, [])

    def test_help_has_every_group_and_opens_once(self):
        win = show_shortcuts(self.root)
        self.root.update()
        text = " ".join(w.cget("text") for card in win.winfo_children()[0].winfo_children()
                        for w in ([card] + card.winfo_children()) if w.winfo_class() in ("Label", "TLabel"))
        for title, rows in SHORTCUT_GROUPS:
            self.assertIn(title, text)
        for key in ("Enter", "Ctrl + S", "Tab / Shift + Tab", "H"):
            self.assertIn(key, text)
        again = show_shortcuts(self.root)
        self.assertIs(again, win)                                     # 두 번 눌러도 창이 하나만 열린다
        win.destroy()
        self.root.update()
        self.assertIsNone(self.root._shortcut_window)

    def test_f1_and_the_tools_menu_open_the_help(self):
        self.assertTrue(self.root.bind("<F1>"))
        self.app.show_help()
        self.assertIsNotNone(self.root._shortcut_window)
        self.root._shortcut_window.destroy()
        bar = self.root.winfo_children()[0]
        menubutton = [w for w in bar.winfo_children() if w.winfo_class() == "TMenubutton"][0]
        menu = self.root.nametowidget(menubutton.cget("menu"))
        labels = [menu.entrycget(i, "label") for i in range(menu.index("end") + 1) if menu.type(i) == "command"]
        self.assertIn("단축키 도움말 (F1)", labels)

    def test_toolbar_buttons_have_tooltips(self):
        for label in ("저장", "저장+다음", "↶ 되돌리기", "삭제", "전체 삭제", "이동 모드"):
            self.assertIn(label, self.app.TOOLTIPS)
            self.assertTrue(self.app.TOOLTIPS[label])
        self.assertIn("Ctrl+S", self.app.TOOLTIPS["저장"])
        self.assertIn("W", self.app.TOOLTIPS["저장+다음"])


if __name__ == "__main__":
    unittest.main()
