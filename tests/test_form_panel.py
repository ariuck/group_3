"""검수 기록 입력칸(라디오 버튼 + 입력칸) 시험.

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_form_panel.py
"""
import tkinter as tk
import unittest
from tkinter import ttk

from src.manifest.manifest_writer import FORM_FIELDS, STATUS_CHOICES
from src.ui.form_panel import SCENE_CHOICES, FormPanel


def radios(widget):
    out = []
    for c in widget.winfo_children():
        if c.winfo_class() == "TRadiobutton":
            out.append(c)
        out += radios(c)
    return out


class FormPanelTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.changes = []
        self.form = FormPanel(self.root, on_change=lambda: self.changes.append(1))
        self.form.pack(fill="x")
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def click(self, text):
        btn = [r for r in radios(self.form) if r.cget("text") == text][0]
        btn.invoke()

    def test_all_choices_are_visible_as_radio_buttons(self):
        names = [r.cget("text") for r in radios(self.form)]
        for label in ["자동", *STATUS_CHOICES, "미정", *SCENE_CHOICES]:
            self.assertIn(label, names)
        self.assertEqual(len(names), 1 + len(STATUS_CHOICES) + 1 + len(SCENE_CHOICES))

    def test_everything_blank_at_first(self):
        v = self.form.get_values()
        self.assertEqual(set(v), {"상태", "이미지 유형", "작성자", "검수자", "발견된 문제", "비고(수정 내용)"})
        self.assertTrue(set(v) <= set(FORM_FIELDS))                   # 검수표에 있는 칸 이름만 쓴다
        self.assertTrue(all(x == "" for x in v.values()))

    def test_clicking_a_radio_sets_the_value_and_reports_a_change(self):
        self.click("수정 필요")
        self.click("정상 김치")
        v = self.form.get_values()
        self.assertEqual((v["상태"], v["이미지 유형"]), ("수정 필요", "정상 김치"))
        self.assertEqual(len(self.changes), 2)

    def test_auto_and_undecided_mean_blank(self):
        self.click("제외")
        self.click("자동")                                            # 사람이 고르지 않은 상태로 되돌린다
        self.assertEqual(self.form.get_values()["상태"], "")
        self.click("판단 어려움")
        self.click("미정")
        self.assertEqual(self.form.get_values()["이미지 유형"], "")

    def test_set_values_fills_radios_and_entries_without_reporting_a_change(self):
        self.form.set_values({"상태": "수정 완료", "이미지 유형": "대상 객체 단독", "작성자": "혜성", "검수자": "동훈",
                              "발견된 문제": "REVIEW: class_ambiguous", "비고(수정 내용)": "메모"})
        self.assertEqual(self.changes, [])                           # 불러오기만 한 것은 '고쳤다' 가 아니다
        v = self.form.get_values()
        self.assertEqual((v["상태"], v["이미지 유형"], v["작성자"], v["검수자"]), ("수정 완료", "대상 객체 단독", "혜성", "동훈"))
        self.assertEqual((v["발견된 문제"], v["비고(수정 내용)"]), ("REVIEW: class_ambiguous", "메모"))

    def test_typing_in_an_entry_reports_a_change(self):
        self.form._vars["작성자"].set("A")
        self.assertEqual(len(self.changes), 1)
        self.assertEqual(self.form.get_values()["작성자"], "A")

    def test_clear(self):
        self.form.set_values({"상태": "제외", "작성자": "A"})
        self.form.clear()
        self.assertTrue(all(x == "" for x in self.form.get_values().values()))

    def test_unknown_or_none_values_become_blank(self):
        self.form.set_values({"상태": None, "작성자": None, "없는 칸": "x"})
        self.assertTrue(all(x == "" for x in self.form.get_values().values()))

    def test_hangul_toggle_button_is_still_there(self):
        def buttons(widget):
            out = []
            for c in widget.winfo_children():
                if c.winfo_class() == "TButton":
                    out.append(c.cget("text"))
                out += buttons(c)
            return out
        texts = buttons(self.form)
        self.assertTrue(any(t.startswith("한/영") for t in texts))
        btn = [c for c in self.form.winfo_children()[0].winfo_children() if c.winfo_class() == "TButton"][0]
        btn.invoke()                                                 # 제목줄의 버튼으로 한글 상태가 바뀐다
        self.assertTrue(self.form.ime.korean)
        self.assertEqual(btn.cget("text"), "한/영: 한글")


if __name__ == "__main__":
    unittest.main()
