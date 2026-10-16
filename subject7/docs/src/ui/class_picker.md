# `src/ui/class_picker.py`

> 오른쪽 위 **클래스** 카드의 Class 선택 목록. 줄마다 색 네모 + 번호 + 이름이며, 고른 줄은 파란 바탕으로 강조한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/class_picker.py)

## 역할

- Class 0~6 을 2열로 보여 주고 클릭으로 고르게 한다.
- 사용하지 않는 Class(4)는 회색으로 보인다. 고르는 것을 막는 일은 [`main_window.choose_class`](main_window.md) 가 한다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `ClassPicker(parent, classes, on_pick, current=0, columns=2)` | `tk.Frame`. `classes` 는 [`settings.CLASSES`](../settings.md) 형식 |
| `.set(cid)` | 선택 표시만 바꿈 (`on_pick` 을 부르지 않음 — 코드에서 선택을 맞출 때) |
| `.get()` | 현재 선택된 Class 번호 |
| `_label(c)` | 이름에서 ` (...)` 설명을 떼어 표시 |

## 의존성

- **사용하는 것**: [`theme`](theme.md)
- **사용하는 곳**: [`main_window`](main_window.md), [`tests/test_theme`](../../tests/test_theme.md)

## 사용 예

```python
picker = ClassPicker(card, settings.CLASSES, on_pick=self.choose_class, current=0)
picker.set(3)          # 선택된 BBox 의 Class 에 맞춰 표시만 바꿈
```

## 주의사항

- 클릭하면 `on_pick(cid)` 만 부른다. 실제 선택 표시는 콜백 쪽에서 `set()` 을 불러야 바뀐다 (사용 안 하는 Class 를 거부할 수 있게).
