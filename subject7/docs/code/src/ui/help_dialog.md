# `src/ui/help_dialog.py`

> 단축키 도움말 창 (`F1`). 화면에 보여 줄 설명과 **실제로 연결된 Tk 키 이름**을 한 표에 함께 적어 둔다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/ui/help_dialog.py)

## 역할

- 단축키를 묶음별(검수 / 사진 이동 / BBox 편집 / 보기 / 도움말) 카드로 보여 준다.
- 표에 적힌 키가 실제로 연결되어 있는지 시험([`test_tooltip_help`](../../tests/test_tooltip_help.md))이 확인하므로, **도움말과 실제 동작이 어긋나지 않는다.**

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `SHORTCUT_GROUPS` | `[(묶음 제목, [(보이는 키, 설명, [Tk 키 이름, ...]), ...]), ...]`. Tk 키 목록이 빈 줄은 마우스 조작 설명 |
| `all_bindings()` | 표에 적힌 Tk 키 이름 전체 (시험용) |
| `show_shortcuts(root)` | 도움말 창을 연다. 이미 열려 있으면 앞으로 가져옴. `Esc`·`F1` 로 닫음 |

### 묶음별 주요 키

| 묶음 | 키 |
|---|---|
| 검수 | `Enter`, `Ctrl+1~4`, `R`, `N`, `W`, `Ctrl+S` |
| 사진 이동 | `← →`, `A D`, `PageUp PageDown`, `Ctrl+G` |
| BBox 편집 | 드래그, `0~6`, `Tab`/`Shift+Tab`, `Shift+방향키`, `Delete`, `Ctrl+Z`/`Ctrl+Y`, `Esc` |
| 보기 | 휠, 오른쪽 드래그, `F`/`Ctrl+0`, `+`/`-`, `H` |
| 도움말 | `F1` |

## 의존성

- **사용하는 것**: [`theme`](theme.md)
- **사용하는 곳**: [`main_window`](main_window.md) (`show_help`), [`tests/test_tooltip_help`](../../tests/test_tooltip_help.md)

## 주의사항

- [`main_window.bind_events`](main_window.md) 에서 단축키를 추가·변경하면 **이 표도 같이 고쳐야** 한다. 그렇지 않으면 시험이 실패한다.
