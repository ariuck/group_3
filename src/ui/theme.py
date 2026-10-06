"""화면 디자인(색·글꼴·위젯 모양)을 한 곳에서 정한다.

    setup(root)        프로그램을 켤 때 한 번 — 글꼴을 고르고 ttk 위젯 모양(버튼·입력칸·표 등)을 정한다
    COLORS             색 이름표. 화면 코드에서는 '#2563eb' 같은 값을 직접 쓰지 않고 COLORS["accent"] 처럼 쓴다
    font(크기, 굵게)   글꼴 튜플.  mono(크기) = 숫자·좌표용 고정폭 글꼴
    card(부모)         흰 바탕에 옅은 테두리를 두른 '카드' 상자

디자인을 바꾸고 싶으면 이 파일의 COLORS 와 setup() 안의 값만 고치면 화면 전체에 적용된다.
"""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

COLORS = {
    "bg": "#eef1f6",          # 창 바탕 (연한 청회색)
    "bar": "#ffffff",         # 위쪽 도구 줄
    "card": "#ffffff",        # 카드 안쪽
    "border": "#d7dde8",      # 옅은 테두리
    "text": "#1f2937",        # 기본 글자
    "muted": "#6b7280",       # 보조 글자
    "faint": "#9ca3af",       # 비활성 글자
    "accent": "#2563eb",      # 강조(파랑) — 현재 선택·주요 버튼
    "accent_hover": "#1d4ed8",
    "accent_soft": "#dbeafe",  # 강조의 옅은 바탕 (선택된 줄)
    "ok": "#16a34a",          # 완료(초록)
    "warn": "#ea580c",        # 변경·수정(주황)
    "danger": "#dc2626",      # 주의·필요(빨강)
    "canvas": "#161a22",      # 이미지 도화지 바탕
    "chip": "#f3f4f6",        # 버튼 기본 바탕
    "chip_hover": "#e5e7eb",
    "chip_down": "#d1d5db",
}

UI_FONTS = ("Malgun Gothic", "Noto Sans CJK KR", "Noto Sans KR", "NanumGothic", "Apple SD Gothic Neo")
MONO_FONTS = ("Consolas", "Noto Sans Mono CJK KR", "DejaVu Sans Mono", "Courier New")

_family = {"ui": "TkDefaultFont", "mono": "TkFixedFont"}


def _pick(root, candidates, fallback):
    have = set(tkfont.families(root))
    return next((f for f in candidates if f in have), fallback)


def font(size=10, bold=False):
    return (_family["ui"], size, "bold" if bold else "normal")


def mono(size=9, bold=False):
    return (_family["mono"], size, "bold" if bold else "normal")


def card(parent, padx=10, pady=8, **kw):
    """흰 바탕 + 옅은 테두리 카드. (안쪽 여백은 padx·pady)"""
    return tk.Frame(parent, bg=COLORS["card"], highlightbackground=COLORS["border"], highlightthickness=1,
                    padx=padx, pady=pady, **kw)


def setup(root):
    """글꼴을 고르고 ttk 위젯 모양을 정한다. 화면을 만들기 전에 한 번 부른다."""
    c = COLORS
    _family["ui"] = _pick(root, UI_FONTS, tkfont.nametofont("TkDefaultFont").actual("family"))
    _family["mono"] = _pick(root, MONO_FONTS, tkfont.nametofont("TkFixedFont").actual("family"))
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkTooltipFont"):
        tkfont.nametofont(name).configure(family=_family["ui"], size=10)
    tkfont.nametofont("TkFixedFont").configure(family=_family["mono"], size=9)
    root.configure(bg=c["bg"])
    root.option_add("*Listbox.background", c["card"])
    root.option_add("*Listbox.selectBackground", c["accent_soft"])
    root.option_add("*Listbox.selectForeground", c["text"])

    s = ttk.Style(root)
    s.theme_use("clam")                                   # 색을 마음대로 바꿀 수 있는 기본 테마
    flat = dict(lightcolor=c["border"], darkcolor=c["border"], bordercolor=c["border"])

    s.configure(".", background=c["bg"], foreground=c["text"], font=font(10), focuscolor=c["bg"],
                troughcolor=c["bg"], **flat)
    s.configure("TFrame", background=c["bg"])
    s.configure("Bar.TFrame", background=c["bar"])
    s.configure("Card.TFrame", background=c["card"])
    s.configure("TLabel", background=c["bg"], foreground=c["text"])
    s.configure("Bar.TLabel", background=c["bar"])
    s.configure("Card.TLabel", background=c["card"])
    s.configure("Muted.TLabel", foreground=c["muted"], font=font(9))
    s.configure("CardMuted.TLabel", background=c["card"], foreground=c["muted"], font=font(9))
    s.configure("CardTitle.TLabel", background=c["card"], foreground=c["text"], font=font(11, True))
    s.configure("Title.TLabel", foreground=c["text"], font=font(13, True))
    s.configure("Diff.TLabel", foreground=c["accent"], font=font(10, True))
    s.configure("Status.TLabel", background=c["bar"], foreground=c["muted"], font=font(9))
    s.configure("Coord.TLabel", background=c["bg"], foreground=c["text"], font=mono(9))
    s.configure("TSeparator", background=c["border"])

    # 버튼: 기본(옅은 회색) · 주요(파랑) · 보조(옅은 파랑) · 위험
    def button(style, bg, fg, hover, down, border=None, padding=(11, 5), font_=None):
        s.configure(style, background=bg, foreground=fg, bordercolor=border or bg, lightcolor=bg, darkcolor=bg,
                    padding=padding, relief="flat", font=font_ or font(10), anchor="center", width=0)   # width=0: 글자 크기대로
        s.map(style, background=[("disabled", c["chip"]), ("pressed", down), ("active", hover)],
              foreground=[("disabled", c["faint"])],
              bordercolor=[("disabled", c["border"]), ("pressed", down), ("active", hover)],
              lightcolor=[("pressed", down), ("active", hover)], darkcolor=[("pressed", down), ("active", hover)])

    button("TButton", c["chip"], c["text"], c["chip_hover"], c["chip_down"], border=c["border"])
    button("Tool.TButton", c["chip"], c["text"], c["chip_hover"], c["chip_down"], border=c["border"], padding=(10, 5))
    button("Tool.TMenubutton", c["chip"], c["text"], c["chip_hover"], c["chip_down"], border=c["border"], padding=(10, 5))
    button("Primary.TButton", c["accent"], "#ffffff", c["accent_hover"], c["accent_hover"], font_=font(10, True))
    button("Soft.TButton", c["accent_soft"], c["accent"], "#bfdbfe", "#93c5fd", font_=font(10, True))
    button("Danger.TButton", c["chip"], c["danger"], "#fee2e2", "#fecaca", border=c["border"], padding=(10, 5))

    # 칩(선택 버튼): 라디오·체크를 '눌러서 고르는 버튼' 모양으로
    for name, bg in (("Chip.Toolbutton", c["card"]), ("BarChip.Toolbutton", c["bar"]), ("SoftChip.Toolbutton", c["bg"])):
        s.configure(name, background=c["chip"], foreground=c["text"], bordercolor=c["border"], lightcolor=c["chip"],
                    darkcolor=c["chip"], padding=(8, 3), relief="flat", font=font(10), anchor="center", width=0)
        s.map(name,
              background=[("selected", "pressed", c["accent_hover"]), ("selected", c["accent"]),
                          ("pressed", c["chip_down"]), ("active", c["chip_hover"])],
              foreground=[("selected", "#ffffff")],
              bordercolor=[("selected", c["accent"]), ("active", c["accent"])],
              lightcolor=[("selected", c["accent"])], darkcolor=[("selected", c["accent"])])

    # 체크박스: 카드 안·도구 줄 안에서 바탕색을 맞춘다
    for name, bg in (("TCheckbutton", c["bg"]), ("Card.TCheckbutton", c["card"]), ("Bar.TCheckbutton", c["bar"]),
                     ("TRadiobutton", c["bg"]), ("Card.TRadiobutton", c["card"])):
        s.configure(name, background=bg, foreground=c["text"], font=font(10), indicatorcolor="#ffffff",
                    indicatormargin=(0, 0, 6, 0), padding=(2, 3))
        s.map(name, background=[("active", bg)], indicatorcolor=[("selected", c["accent"]), ("pressed", c["accent_soft"])])

    # 입력칸
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        s.configure(name, fieldbackground="#ffffff", background="#ffffff", foreground=c["text"],
                    bordercolor=c["border"], lightcolor="#ffffff", darkcolor="#ffffff", padding=(7, 4),
                    insertcolor=c["text"], selectbackground=c["accent_soft"], selectforeground=c["text"])
        s.map(name, bordercolor=[("focus", c["accent"])], lightcolor=[("focus", c["accent"])],
              darkcolor=[("focus", c["accent"])], fieldbackground=[("disabled", c["chip"])])
    s.configure("Nav.TEntry", padding=(4, 4), justify="center")

    # 표
    s.configure("Treeview", background=c["card"], fieldbackground=c["card"], foreground=c["text"], rowheight=26,
                borderwidth=0, font=font(10), **{k: c["card"] for k in ("lightcolor", "darkcolor", "bordercolor")})
    s.map("Treeview", background=[("selected", c["accent_soft"])], foreground=[("selected", c["text"])])
    s.configure("Treeview.Heading", background=c["bg"], foreground=c["muted"], relief="flat", font=font(9, True),
                padding=(6, 5), bordercolor=c["bg"], lightcolor=c["bg"], darkcolor=c["bg"])
    s.map("Treeview.Heading", background=[("active", c["chip_hover"])])

    # 스크롤바
    s.configure("Vertical.TScrollbar", background=c["chip_hover"], troughcolor=c["bg"], bordercolor=c["bg"],
                arrowcolor=c["muted"], lightcolor=c["chip_hover"], darkcolor=c["chip_hover"])
    return s
