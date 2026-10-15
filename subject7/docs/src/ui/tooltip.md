# `src/ui/tooltip.py`

> 버튼 위에 마우스를 잠깐 올려 두면 뜨는 설명 말풍선.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/tooltip.py)

## 역할

- 도구 줄 버튼·이전/다음 버튼·번호 입력칸 등에 짧은 설명과 단축키를 보여 준다.
- 글자 대신 함수를 넘기면 말풍선이 뜰 때마다 그 함수가 돌려준 글자를 보여 준다 (상황에 따라 바뀌는 설명).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `Tooltip(widget, text, delay=550)` | `text` 는 문자열 또는 함수. 마우스가 들어오고 550ms 뒤 표시 |
| `.show()` | 제목줄 없는 작은 창(`Toplevel`)을 위젯 아래에 띄움. 글자가 비었거나 이미 떠 있으면 무시 |
| `._hide()` | 마우스가 나가거나·클릭하거나·위젯이 사라지면 닫음 (예약도 취소) |
| `cancel_all()` | 떠 있거나 예약된 말풍선을 모두 없앰. 창을 닫기 직전에 부른다 |

모든 `Tooltip` 은 `weakref.WeakSet` 으로 추적하므로 위젯이 사라지면 자동으로 목록에서 빠진다.

## 의존성

- **사용하는 것**: [`theme`](theme.md)
- **사용하는 곳**: [`main_window`](main_window.md), [`tests/test_tooltip_help`](../../tests/test_tooltip_help.md)

## 사용 예

```python
from src.ui.tooltip import Tooltip

Tooltip(save_btn, "Ctrl+S — 지금의 BBox 와 검수 기록을 저장해요")
Tooltip(chip, lambda: "켜짐" if var.get() else "꺼짐")
```

## 주의사항

- 기존 이벤트 연결을 지우지 않도록 `bind(..., add=True)` 로 붙인다.
- 창을 닫을 때 `cancel_all()` 을 부르지 않으면, 예약된 말풍선이 닫힌 창을 찾다가 `invalid command name` 오류를 낼 수 있다.
