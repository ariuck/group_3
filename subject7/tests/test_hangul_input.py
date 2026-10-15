"""한글 조합기 점검 (WSL 에서 영문 자판으로 한글 입력).

    python tests/test_hangul_input.py
"""
import sys
import time
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


def focus(widget):
    """widget 이 실제로 키보드 포커스를 받을 때까지 기다린다.
    (가짜 키 입력은 포커스를 가진 창으로 전달되므로, 포커스가 잡히기 전에 보내면 글자가 사라져 시험이 가끔 실패한다)"""
    widget.focus_force()
    for _ in range(200):
        root.update()
        if root.focus_get() is widget:
            return True
        time.sleep(0.01)
    return False


def press(keysym, char="", state=0):
    focus(entry)
    entry.event_generate("<KeyPress>", keysym=keysym, state=state, when="now")
    root.update()


def tap(keysym):
    """한/영 키를 사람이 누르는 것처럼: 이전 입력과 간격을 두고 누른다 (꾹 눌러 되풀이되는 신호와 구별되도록)."""
    time.sleep(0.2)
    press(keysym)


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
tap("Hangul")
ok("한/영 키로 영어 전환", not ime.korean)

# Shift 를 눌러도 조합이 끊기지 않는다 (ㅖ = Shift+ㅔ, 'ㅎ' 다음에 Shift 를 누르면 예전에는 '혜' 가 'ㅎㅖ' 로 갈라졌다)
tap("Hangul")
var.set("")
ime.finish()
entry.icursor("end")


def type_shifted(seq):
    """seq 의 각 글자를 실제 키보드처럼 친다. 대문자는 Shift 를 먼저 눌렀다가 글자를 누른다."""
    for ch in seq:
        if ch.isupper():
            press("Shift_L", "", state=0)
            press(ch, ch, state=1)
        else:
            press(ch, ch)


type_shifted("gPtjd")            # ㅎ + Shift+ㅔ(ㅖ) + ㅅㅓㅇ  →  혜성
ok(f"Shift 를 눌러도 이어서 조합: 혜성 (got {var.get()!r})", var.get() == "혜성")
var.set(""); ime.finish(); entry.icursor("end")
type_shifted("Rkcl")             # 쌍자음 ㄲ (Shift+r) + ㅏ + ㅊ + ㅣ  →  까치
ok(f"쌍자음도 Shift 로 정상 입력: 까치 (got {var.get()!r})", var.get() == "까치")
var.set(""); ime.finish(); entry.icursor("end")
for ch in "gk":
    press(ch, ch)
press("Shift_R", "")             # 조합 중간에 Shift 만 눌렀다 떼도 글자가 그대로 이어진다
press("Caps_Lock", "")
press("s", "s")
ok(f"조합 중 Shift·CapsLock 만 눌러도 유지: 한 (got {var.get()!r})", var.get() == "한")
tap("Hangul")

# ── 한/영 키: 눌렀다 떼면 한 번만 바뀐다 / 떼는 신호만 와도 바뀐다 / 이미지 화면(입력칸이 아닌 곳)에서도 바뀐다 ──
def release(keysym):
    focus(entry)
    entry.event_generate("<KeyRelease>", keysym=keysym, when="now")
    root.update()


before = ime.korean
time.sleep(0.2)
press("Hangul"); release("Hangul")
ok("한/영 키를 눌렀다 떼면 한 번만 바뀐다", ime.korean != before)
before = ime.korean
press("Hangul"); press("Hangul"); press("Hangul")      # 꾹 눌러서 짧은 간격으로 되풀이되는 신호
release("Hangul")
ok("꾹 눌러 되풀이되는 신호는 한 번으로 친다", ime.korean != before)
before = ime.korean
tap("Hangul")                                          # 떼는 신호가 오지 않는 환경: 누를 때마다 바뀐다
tap("Hangul")
ok("떼는 신호가 없어도 누를 때마다 바뀐다 (두 번 누르면 원래대로)", ime.korean == before)
before = ime.korean
ime._toggle_down.clear()                             # (떼는 신호만 오는 환경을 흉내: 눌린 기록이 없다)
release("Hangul")                                    # 누르는 신호 없이 떼는 신호만 온 경우 (Windows 가 가로챈 경우)
ok("떼는 신호만 와도 바뀐다", ime.korean != before)
before = ime.korean
time.sleep(0.2)
press("Alt_R"); release("Alt_R")
ok("오른쪽 Alt 도 한/영 키처럼 한 번만 바뀐다", ime.korean != before)

other = tk.Frame(root, width=50, height=20)          # 입력칸이 아닌 곳 (이미지 화면 대신)
other.pack()
ime.bind_global(root)
ok("입력칸이 아닌 곳(이미지 화면 대신)에 포커스가 잡힘", focus(other))
before = ime.korean
time.sleep(0.2)
other.event_generate("<KeyPress>", keysym="Hangul", when="now"); root.update()
other.event_generate("<KeyRelease>", keysym="Hangul", when="now"); root.update()
ok("입력칸이 아닌 곳에서도 한/영 키로 바뀐다", ime.korean != before)
before = ime.korean
time.sleep(0.2)
focus(entry)
entry.event_generate("<KeyPress>", keysym="Hangul", when="now"); root.update()
entry.event_generate("<KeyRelease>", keysym="Hangul", when="now"); root.update()
ok("입력칸에서는 두 번 바뀌지 않는다 (전체 연결과 겹치지 않음)", ime.korean != before)

root.destroy()
sys.exit(1 if failed else 0)
