"""입력칸 안에서 쓰는 두벌식 한글 조합기.

WSL 에는 한글 입력기(IME)가 없어서 tkinter 입력칸에 영어만 들어간다.
그래서 영문 자판 글자(r, k, s ...)를 프로그램이 직접 받아 한글(ㄱ, ㅏ, ㄴ ...)로 조합한다.

    한/영 전환: 한/영 키, 오른쪽 Alt, Shift+Space, 또는 [한/영] 버튼
    Windows 쪽 입력기는 '영어(A)' 상태로 두고 쓴다.

form_panel 에서 쓰는 방법
    ime = HangulIME()
    ime.attach(entry)          # 한글을 받을 입력칸마다
"""
import tkinter as tk

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = ["", *"ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"]

# 두벌식 자판: 영문 글자 → 자모
KEYMAP = {
    "q": "ㅂ", "w": "ㅈ", "e": "ㄷ", "r": "ㄱ", "t": "ㅅ", "y": "ㅛ", "u": "ㅕ", "i": "ㅑ", "o": "ㅐ", "p": "ㅔ",
    "a": "ㅁ", "s": "ㄴ", "d": "ㅇ", "f": "ㄹ", "g": "ㅎ", "h": "ㅗ", "j": "ㅓ", "k": "ㅏ", "l": "ㅣ",
    "z": "ㅋ", "x": "ㅌ", "c": "ㅊ", "v": "ㅍ", "b": "ㅠ", "n": "ㅜ", "m": "ㅡ",
    "Q": "ㅃ", "W": "ㅉ", "E": "ㄸ", "R": "ㄲ", "T": "ㅆ", "O": "ㅒ", "P": "ㅖ",
}

VOWEL_PAIRS = {("ㅗ", "ㅏ"): "ㅘ", ("ㅗ", "ㅐ"): "ㅙ", ("ㅗ", "ㅣ"): "ㅚ",
               ("ㅜ", "ㅓ"): "ㅝ", ("ㅜ", "ㅔ"): "ㅞ", ("ㅜ", "ㅣ"): "ㅟ", ("ㅡ", "ㅣ"): "ㅢ"}
FINAL_PAIRS = {("ㄱ", "ㅅ"): "ㄳ", ("ㄴ", "ㅈ"): "ㄵ", ("ㄴ", "ㅎ"): "ㄶ", ("ㄹ", "ㄱ"): "ㄺ", ("ㄹ", "ㅁ"): "ㄻ",
               ("ㄹ", "ㅂ"): "ㄼ", ("ㄹ", "ㅅ"): "ㄽ", ("ㄹ", "ㅌ"): "ㄾ", ("ㄹ", "ㅍ"): "ㄿ", ("ㄹ", "ㅎ"): "ㅀ",
               ("ㅂ", "ㅅ"): "ㅄ"}
VOWEL_SPLIT = {v: k for k, v in VOWEL_PAIRS.items()}
FINAL_SPLIT = {v: k for k, v in FINAL_PAIRS.items()}


def jamo_for(char):
    """영문 글자 하나를 자모로. 대문자는 쌍자음·ㅒ·ㅖ 말고는 소문자와 같다 (Caps Lock 대비)."""
    return KEYMAP.get(char) or KEYMAP.get(char.lower())


class Composer:
    """한 글자(음절)를 조합하는 상태. 화면과는 상관없이 글자 계산만 한다."""

    def __init__(self):
        self.cho = self.jung = self.jong = ""

    @property
    def active(self):
        return bool(self.cho or self.jung)

    def text(self):
        """지금 조합 중인 글자 (없으면 빈 문자열)."""
        if self.cho and self.jung:
            code = 0xAC00 + (CHO.index(self.cho) * 21 + JUNG.index(self.jung)) * 28 + JONG.index(self.jong)
            return chr(code)
        return self.cho or self.jung

    def reset(self):
        self.cho = self.jung = self.jong = ""

    def add(self, jamo):
        """자모 하나를 넣는다. 다 만들어져 확정된 글자를 돌려준다 (없으면 "")."""
        if jamo in JUNG:
            return self._add_vowel(jamo)
        return self._add_consonant(jamo)

    def _add_consonant(self, c):
        if self.cho and self.jung and not self.jong and c in JONG:
            self.jong = c                                    # 받침
            return ""
        if self.jong and (self.jong, c) in FINAL_PAIRS:
            self.jong = FINAL_PAIRS[(self.jong, c)]          # 겹받침 (ㄹ+ㄱ → ㄺ)
            return ""
        done = self.text()
        self.reset()
        self.cho = c
        return done

    def _add_vowel(self, v):
        if self.jong:                                        # 받침이 다음 글자 첫소리로 넘어간다 (갑+ㅏ → 가바)
            first, moved = FINAL_SPLIT.get(self.jong, ("", self.jong))
            self.jong = first
            done = self.text()
            self.reset()
            self.cho, self.jung = moved, v
            return done
        if self.jung:
            if (self.jung, v) in VOWEL_PAIRS:
                self.jung = VOWEL_PAIRS[(self.jung, v)]      # ㅗ+ㅏ → ㅘ
                return ""
            done = self.text()
            self.reset()
            self.jung = v
            return done
        if self.cho:
            self.jung = v
            return ""
        self.jung = v
        return ""

    def backspace(self):
        """조합 중인 글자를 한 단계 지운다. 지울 것이 없었으면 False."""
        if self.jong:
            self.jong = FINAL_SPLIT.get(self.jong, ("",))[0]
        elif self.jung:
            self.jung = VOWEL_SPLIT.get(self.jung, ("",))[0]
        elif self.cho:
            self.cho = ""
        else:
            return False
        return True


def compose(keys):
    """영문 자판 입력을 한글로 바꾼 결과 (시험용). 예: compose("rkskek") == "가나다" """
    comp, out = Composer(), ""
    for ch in keys:
        jamo = jamo_for(ch)
        if jamo:
            out += comp.add(jamo)
        else:
            out += comp.text() + ch
            comp.reset()
    return out + comp.text()


TOGGLE_KEYSYMS = {"Hangul", "Alt_R"}      # WSL 에서 한/영 키는 보통 둘 중 하나로 들어온다
CONTROL, ALT = 0x0004, 0x0008             # event.state 의 Ctrl·Alt 비트


class HangulIME:
    """여러 입력칸이 함께 쓰는 한/영 상태. 켜져 있으면 영문 글자를 한글로 조합해 넣는다."""

    def __init__(self, on_mode_change=None):
        self.korean = False
        self._on_mode_change = on_mode_change
        self._comp = Composer()
        self._entry = None          # 지금 조합 중인 입력칸
        self._start = 0             # 조합 중인 글자의 위치
        self._shown = 0             # 화면에 보이는 조합 글자 수 (0 또는 1)

    def toggle(self):
        self.finish()
        self.korean = not self.korean
        if self._on_mode_change:
            self._on_mode_change(self.korean)

    def attach(self, entry):
        entry.bind("<KeyPress>", self._on_key, add=True)
        for seq in ("<FocusOut>", "<ButtonPress>"):
            entry.bind(seq, lambda e: self.finish(), add=True)

    def finish(self):
        """조합 중인 글자를 그대로 확정한다 (커서 이동·클릭·포커스 이동 때)."""
        self._comp.reset()
        self._entry, self._shown = None, 0

    def _on_key(self, event):
        entry = event.widget
        if event.keysym in TOGGLE_KEYSYMS or (event.keysym == "space" and event.state & 0x0001):
            self.toggle()
            return "break"
        if not self.korean or event.state & (CONTROL | ALT):
            return None                                       # Ctrl+V 붙여 넣기 등은 원래대로
        # 다른 칸이거나 커서가 옮겨졌으면 이전 조합은 끝난 것으로 본다
        if self._entry is not entry or entry.index(tk.INSERT) != self._start + self._shown:
            self.finish()

        if event.keysym == "BackSpace" and self._comp.active:
            self._comp.backspace()
            self._render(entry, "")
            return "break"

        jamo = jamo_for(event.char) if len(event.char) == 1 else None
        if not jamo:
            self.finish()                                     # 숫자·공백·기호·방향키는 원래대로 들어간다
            return None

        if entry.selection_present():
            entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.finish()
        if self._entry is None:
            self._entry, self._start = entry, entry.index(tk.INSERT)
        self._render(entry, self._comp.add(jamo))
        return "break"

    def _render(self, entry, done):
        """조합 중이던 글자를 지우고, 확정된 글자 + 새 조합 글자를 넣는다."""
        entry.delete(self._start, self._start + self._shown)
        now = self._comp.text()
        entry.insert(self._start, done + now)
        self._start += len(done)
        self._shown = len(now)
        entry.icursor(self._start + self._shown)
        if not self._comp.active:
            self.finish()
