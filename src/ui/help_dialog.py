"""단축키 도움말 (F1).

SHORTCUT_GROUPS 는 '화면에 보여 줄 설명'과 '실제로 연결된 키(Tk 표기)'를 함께 적어 둔 표다.
시험(tests/test_tooltip_help.py)이 여기 적힌 키가 모두 실제로 연결되어 있는지 확인하므로, 단축키를 바꾸면 이 표도 같이 고쳐야 한다.
"""
import tkinter as tk
from tkinter import ttk

from src.ui import theme

# (눌러야 하는 키 — 화면에 보이는 글자, 하는 일, 실제 연결된 Tk 키 이름 목록)
SHORTCUT_GROUPS = [
    ("검수 (한 키로 빠르게)", [
        ("Enter", "이 사진은 끝 — 저장하고 다음 사진으로 (원본과 같으면 '검수 완료', 고쳤으면 '수정 완료')", ["<Return>"]),
        ("R", "수정 필요로 표시하고 이유 쓰기 (이유를 쓰고 Enter 를 누르면 저장하고 다음으로)", ["r", "R"]),
        ("N", "아직 작업하지 않은 다음 사진으로 건너뛰기", ["n", "N"]),
        ("W", "저장하고 다음 사진으로 (상태는 그대로)", ["w", "W"]),
        ("Ctrl + S", "저장", ["<Control-s>"]),
    ]),
    ("사진 이동", [
        ("← →  /  A D  /  PageUp PageDown", "이전·다음 사진 (꾹 눌러도 밀리지 않아요)", ["<Left>", "<Right>", "a", "d", "<Prior>", "<Next>"]),
        ("Ctrl + G", "사진 번호를 입력해서 바로 이동", ["<Control-g>"]),
    ]),
    ("BBox 편집", [
        ("드래그", "빈 곳 = 새 BBox, BBox 안쪽 = 이동, 흰 점(핸들) = 크기 조절, Shift + 드래그 = 겹쳐서 새 BBox", []),
        ("0 ~ 6", "Class 선택 (BBox 가 선택되어 있으면 그 BBox 의 Class 변경)", ["0", "1", "2", "3", "4", "5", "6"]),
        ("Tab / Shift + Tab", "다음·이전 BBox 선택", ["<Tab>", "<Shift-Tab>"]),
        ("Shift + 방향키", "선택한 BBox 를 1px 이동 (Ctrl 도 누르면 10px)", ["<Shift-Left>", "<Control-Shift-Left>"]),
        ("Delete", "선택한 BBox 삭제", ["<Delete>"]),
        ("Ctrl + Z  /  Ctrl + Y", "되돌리기 / 다시 실행", ["<Control-z>", "<Control-y>"]),
        ("Esc", "드래그 취소, 아니면 선택 해제", ["<Escape>"]),
    ]),
    ("보기", [
        ("마우스 휠", "확대·축소 (커서 위치 기준)", []),
        ("오른쪽 버튼 드래그", "화면 이동 (툴바의 '이동 모드'를 켜면 왼쪽 버튼으로도 가능)", []),
        ("F  /  Ctrl + 0", "이미지 전체가 보이게 맞춤", ["f", "F", "<Control-Key-0>"]),
        ("+  /  -", "확대 / 축소", ["<plus>", "<minus>"]),
        ("H", "BBox 숨기기·보이기", ["h", "H"]),
    ]),
    ("도움말", [
        ("F1", "이 도움말 열기", ["<F1>"]),
    ]),
]


def all_bindings():
    """도움말 표에 적힌 Tk 키 이름 전체 (시험에서 실제 연결 여부를 확인하는 데 쓴다)."""
    return [seq for _title, rows in SHORTCUT_GROUPS for _keys, _desc, seqs in rows for seq in seqs]


def show_shortcuts(root):
    """단축키 도움말 창을 연다. 이미 열려 있으면 앞으로 가져온다."""
    existing = getattr(root, "_shortcut_window", None)
    if existing is not None:
        try:
            existing.deiconify()
            existing.lift()
            existing.focus_set()
            return existing
        except tk.TclError:
            pass
    C = theme.COLORS
    win = tk.Toplevel(root)
    win.title("단축키 도움말")
    win.configure(bg=C["bg"])
    win.transient(root)
    root._shortcut_window = win
    win.bind("<Destroy>", lambda e: setattr(root, "_shortcut_window", None) if e.widget is win else None)
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<F1>", lambda e: win.destroy())

    body = ttk.Frame(win, padding=(18, 14))
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="단축키", style="Title.TLabel").pack(anchor="w")
    ttk.Label(body, text="입력칸에 글자를 치는 동안에는 글자 단축키(W A D F H N R 숫자 등)가 동작하지 않아요.",
              style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

    for title, rows in SHORTCUT_GROUPS:
        card = theme.card(body, padx=12, pady=8)
        card.pack(fill="x", pady=(0, 8))
        tk.Label(card, text=title, bg=C["card"], fg=C["text"], font=theme.font(10, True)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        for i, (keys, desc, _seqs) in enumerate(rows, start=1):
            tk.Label(card, text=keys, bg=C["chip"], fg=C["text"], font=theme.mono(9, True), padx=8, pady=2,
                     anchor="w").grid(row=i, column=0, sticky="w", pady=2, padx=(0, 12))
            tk.Label(card, text=desc, bg=C["card"], fg=C["text"], font=theme.font(10), anchor="w",
                     justify="left", wraplength=560).grid(row=i, column=1, sticky="w", pady=2)
        card.columnconfigure(0, minsize=250)                      # 카드마다 설명이 같은 위치에서 시작하도록 키 열 폭을 맞춘다
        card.columnconfigure(1, weight=1)

    ttk.Button(body, text="닫기 (Esc)", command=win.destroy, style="Tool.TButton").pack(anchor="e", pady=(4, 0))
    win.update_idletasks()
    win.geometry(f"+{root.winfo_rootx() + 80}+{root.winfo_rooty() + 40}")
    return win
