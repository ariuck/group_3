"""디자인 체계(theme)와 Class 선택 위젯 시험.

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_theme.py
"""
import tkinter as tk
import unittest
from tkinter import ttk

from src import settings
from src.ui import theme
from src.ui.class_picker import ClassPicker


class ThemeTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")

    def tearDown(self):
        self.root.destroy()

    def test_setup_picks_a_font_and_defines_the_styles(self):
        style = theme.setup(self.root)
        self.assertEqual(style.theme_use(), "clam")
        family = theme.font(10)[0]
        self.assertTrue(family)
        for name in ("Primary.TButton", "Soft.TButton", "Tool.TButton", "Danger.TButton", "Chip.Toolbutton", "Nav.TEntry"):
            self.assertTrue(style.lookup(name, "background") or style.lookup(name, "padding"), name)
        self.assertEqual(style.lookup("Primary.TButton", "background"), theme.COLORS["accent"])

    def test_buttons_are_sized_by_their_text(self):
        style = theme.setup(self.root)
        for name in ("Tool.TButton", "Primary.TButton"):
            self.assertEqual(str(style.lookup(name, "width")), "0")          # 모든 버튼이 같은 폭으로 늘어나지 않는다

    def test_colors_are_valid_hex_values(self):
        for key, value in theme.COLORS.items():
            self.assertRegex(value, r"^#[0-9a-fA-F]{6}$", key)

    def test_card_has_a_border(self):
        theme.setup(self.root)
        c = theme.card(self.root)
        self.assertEqual(int(c.cget("highlightthickness")), 1)
        self.assertEqual(c.cget("bg"), theme.COLORS["card"])

    def test_widgets_can_be_built_with_every_custom_style(self):
        theme.setup(self.root)
        for style, cls in (("Tool.TButton", ttk.Button), ("Primary.TButton", ttk.Button), ("Soft.TButton", ttk.Button),
                           ("Danger.TButton", ttk.Button), ("Chip.Toolbutton", ttk.Checkbutton),
                           ("Nav.TEntry", ttk.Entry), ("Title.TLabel", ttk.Label), ("Diff.TLabel", ttk.Label)):
            cls(self.root, style=style)                                       # 스타일 이름이 틀리면 여기서 오류가 난다


class ClassPickerTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        theme.setup(self.root)
        self.picked = []
        self.picker = ClassPicker(self.root, settings.CLASSES, on_pick=self.picked.append, current=2)
        self.picker.pack()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_shows_every_class_and_the_current_one_is_highlighted(self):
        self.assertEqual(sorted(self.picker._rows), [c["id"] for c in settings.CLASSES])
        self.assertEqual(self.picker.get(), 2)
        row, _chip, _name = self.picker._rows[2]
        self.assertEqual(row.cget("bg"), theme.COLORS["accent_soft"])
        self.assertEqual(self.picker._rows[0][0].cget("bg"), theme.COLORS["card"])

    def test_click_reports_the_class_number(self):
        for part in range(3):                                                # 줄 · 색 네모 · 이름 어디를 눌러도 같다
            self.picked.clear()
            self.picker._rows[5][part].event_generate("<Button-1>", x=3, y=3)
            self.root.update()
            self.assertEqual(self.picked, [5])

    def test_set_changes_only_the_highlight(self):
        self.picker.set(6)
        self.assertEqual(self.picker.get(), 6)
        self.assertEqual(self.picker._rows[6][0].cget("bg"), theme.COLORS["accent_soft"])
        self.assertEqual(self.picker._rows[2][0].cget("bg"), theme.COLORS["card"])
        self.assertEqual(self.picked, [])                                    # 코드로 바꾼 것은 '눌렀다'로 알리지 않는다

    def test_unused_class_is_gray(self):
        unused = [c for c in settings.CLASSES if not c["enabled"]][0]["id"]
        _row, chip, name = self.picker._rows[unused]
        self.assertEqual(name.cget("fg"), theme.COLORS["faint"])
        self.assertEqual(chip.cget("bg"), theme.COLORS["faint"])


if __name__ == "__main__":
    unittest.main()
