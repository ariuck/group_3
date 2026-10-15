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

    # ── 작성자·검수자 이름 기억 (프로그램을 켜 둔 동안만, 파일에는 저장하지 않음) ───────────────────
    def type_name(self, key, text):
        self.form._vars[key].set(text)                               # 사람이 입력칸에 쓴 것과 같은 경로(write 추적)

    def test_names_typed_by_the_person_fill_blank_cells_of_the_next_photo(self):
        self.type_name("검수자", "손상우")
        self.form.set_values({"상태": "검수 전", "작성자": "이후영"})            # 다른 사진을 열었다 (검수자 칸이 비어 있음)
        self.form.fill_remembered()
        v = self.form.get_values()
        self.assertEqual((v["작성자"], v["검수자"], v["상태"]), ("이후영", "손상우", "검수 전"))

    def test_existing_names_are_never_overwritten(self):
        self.type_name("검수자", "손상우")
        self.type_name("작성자", "강동연")
        self.form.set_values({"작성자": "이후영", "검수자": "지혜성"})          # 이미 이름이 적힌 사진
        self.form.fill_remembered()
        v = self.form.get_values()
        self.assertEqual((v["작성자"], v["검수자"]), ("이후영", "지혜성"))

    def test_own_photo_is_not_prefilled_as_reviewer_and_vice_versa(self):
        self.type_name("검수자", "손상우")
        self.form.set_values({"작성자": "손상우"})                            # 내가 쓴 사진
        self.form.fill_remembered()
        self.assertEqual(self.form.get_values()["검수자"], "")                # 자기 사진을 자기가 검수하지 않게 비워 둔다
        self.type_name("작성자", "김석범")
        self.form.set_values({"검수자": "김석범"})
        self.form.fill_remembered()
        self.assertEqual(self.form.get_values()["작성자"], "")

    def test_prefilling_is_not_a_change_and_does_not_change_the_memory(self):
        self.type_name("검수자", "손상우")
        self.changes.clear()
        self.form.set_values({"작성자": "이후영"})
        self.form.fill_remembered()
        self.assertEqual(self.changes, [])                           # '저장 안 됨' 이 뜨지 않는다
        self.form.set_values({"검수자": "지혜성"})                       # 불러온 값은 기억을 바꾸지 않는다
        self.form.set_values({})
        self.form.fill_remembered()
        self.assertEqual(self.form.get_values()["검수자"], "손상우")

    def test_clearing_the_cell_by_hand_stops_the_memory(self):
        self.type_name("검수자", "손상우")
        self.type_name("검수자", "")                                   # 사람이 지웠다
        self.form.set_values({"작성자": "이후영"})
        self.form.fill_remembered()
        self.assertEqual(self.form.get_values()["검수자"], "")
        self.type_name("검수자", "김동훈")                              # 이름을 바꾸면 다음 사진부터 새 이름
        self.form.set_values({"작성자": "이후영"})
        self.form.fill_remembered()
        self.assertEqual(self.form.get_values()["검수자"], "김동훈")

    def test_other_cells_are_not_remembered(self):
        self.type_name("발견된 문제", "REVIEW: class_ambiguous")
        self.click("수정 필요")
        self.form.set_values({})
        self.form.fill_remembered()
        v = self.form.get_values()
        self.assertEqual((v["발견된 문제"], v["상태"]), ("", ""))

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
