# `src/ui/theme.py`

> 화면 디자인(색·글꼴·위젯 모양)을 한 곳에서 정한다. 색이나 글꼴을 바꾸려면 이 파일만 고치면 된다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/ui/theme.py)

## 역할

- 화면 코드에서 `'#2563eb'` 같은 값을 직접 쓰지 않고 `COLORS["accent"]` 처럼 이름으로 쓰게 한다.
- 한글 글꼴을 PC 에 있는 것 중에서 고른다 (Windows / WSL / macOS 공통).
- ttk 위젯 스타일(버튼·칩·입력칸·표·스크롤바)을 `clam` 테마 위에 정의한다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `COLORS` | `bg`, `bar`, `card`, `border`, `text`, `muted`, `faint`, `accent`(파랑), `accent_soft`, `ok`(초록), `warn`(주황), `danger`(빨강), `canvas`, `chip` … |
| `UI_FONTS`, `MONO_FONTS` | 후보 글꼴 (Malgun Gothic → Noto Sans CJK KR → …, Consolas → …) |
| `font(size=10, bold=False)` | UI 글꼴 튜플 |
| `mono(size=9, bold=False)` | 숫자·좌표용 고정폭 글꼴 튜플 |
| `card(parent, padx, pady)` | 흰 바탕 + 옅은 테두리 `tk.Frame` |
| `setup(root)` | 프로그램 시작 시 한 번. 글꼴 선택, Tk 기본 글꼴 변경, ttk 스타일 정의. `ttk.Style` 반환 |

### 정의하는 스타일

| 종류 | 스타일 이름 |
|---|---|
| 글자 | `Title`, `Muted`, `Card*`, `Diff`, `Warn`, `Dirty`, `Status`, `Coord` (`.TLabel`) |
| 버튼 | `TButton`, `Tool`, `Primary`(파랑), `Soft`(옅은 파랑), `Danger` (`.TButton`), `Tool.TMenubutton` |
| 칩 | `Chip`, `BarChip`, `SoftChip` (`.Toolbutton`) — 라디오·체크를 눌러서 고르는 버튼 모양으로 |
| 기타 | 체크/라디오, `TEntry`·`TCombobox`·`TSpinbox`, `Nav.TEntry`, `Treeview`, `Vertical.TScrollbar` |

## 의존성

- **사용하는 것**: `tkinter`, `tkinter.font`, `ttk`
- **사용하는 곳**: [`main_window`](main_window.md), [`form_panel`](form_panel.md), [`class_picker`](class_picker.md), [`thumb_strip`](thumb_strip.md), [`tooltip`](tooltip.md), [`help_dialog`](help_dialog.md), [`tests/test_theme`](../../tests/test_theme.md), [`tests/test_tooltip_help`](../../tests/test_tooltip_help.md)

## 주의사항

- `font()` / `mono()` 는 `setup()` 을 부르기 전에는 Tk 기본 글꼴 이름을 돌려준다. 위젯을 만들기 전에 `setup()` 을 먼저 부른다.
- [`validation_dialog`](validation_dialog.md) 는 이 테마를 쓰지 않고 `Malgun Gothic` 과 색을 직접 지정한다.
