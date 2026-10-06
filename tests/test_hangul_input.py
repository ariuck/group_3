"""한글 조합기 점검 (WSL 에서 영문 자판으로 한글 입력).

    python tests/test_hangul_input.py
"""
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ui.hangul_input import HangulIME, compose  # noqa: E402

failed = 0


def ok(name, cond):
    global failed
    print(("PASS " if cond else "FAIL ") + name)
    failed += not cond


# 글자 조합 규칙
for keys, want in [
    ("rkskek", "가나다"), ("gksrmf", "한글"), ("rjatnwk", "검수자"), ("dkswjd", "안정"),
    ("rkqt", "값"), ("rkqtdl", "값이"), ("dlfrdj", "읽어"), ("rhkdl", "과이"), ("dmlfh", "의로"),
    ("Rkcl", "까치"), ("RKSK", "까나"), ("ehs 123", "돈 123"), ("r", "ㄱ"), ("k", "ㅏ"),
]:
    got = compose(keys)
    ok(f"compose({keys!r}) == {want!r}  (got {got!r})", got == want)

# 실제 입력칸에 키를 눌러 본다
try:
    root = tk.Tk()
except tk.TclError:
    print("SKIP 화면이 없어 입력칸 시험은 건너뜀")
    sys.exit(1 if failed else 0)
root.geometry("+0+0")
var = tk.StringVar()
entry = ttk.Entry(root, textvariable=var)
entry.pack()
ime = HangulIME()
ime.attach(entry)
entry.focus_force()
root.after(300, root.quit)   # 창이 뜨고 입력칸이 포커스를 받을 때까지 잠깐 기다린다
root.mainloop()


def press(keysym, char="", state=0):
    entry.focus_force()
    root.update()
    entry.event_generate("<KeyPress>", keysym=keysym, state=state, when="now")
    root.update()


for ch in "abc":
    press(ch, ch)
ok("영어 상태: 그대로 영어", var.get() == "abc")

press("space", " ", state=1)          # Shift+Space → 한글
ok("Shift+Space 로 한글 전환", ime.korean)
for ch in "rjatnwk":
    press(ch, ch)
ok(f"검수자 입력 (got {var.get()!r})", var.get() == "abc검수자")
press("BackSpace")
ok(f"BackSpace 한 단계 (got {var.get()!r})", var.get() == "abc검수ㅈ")
press("BackSpace")
press("BackSpace")
ok(f"조합 끝나면 보통 지우기 (got {var.get()!r})", var.get() == "abc검")
press("space", " ")
press("1", "1")
ok(f"공백·숫자는 그대로 (got {var.get()!r})", var.get() == "abc검 1")
press("Hangul")
ok("한/영 키로 영어 전환", not ime.korean)

root.destroy()
sys.exit(1 if failed else 0)
