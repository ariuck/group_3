# `src/bbox/history.py`

> BBox 편집 되돌리기(Undo) / 다시 실행(Redo). 변경 직전의 BBox 목록 전체를 사본으로 쌓는 스냅샷 방식.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/bbox/history.py)

## 역할

- 추가·삭제·이동·크기 조절·Class 변경·전체 삭제를 모두 같은 방법으로 되돌린다.
- 이미지 1장의 BBox 는 많아야 수십 개라서, 명령(command)을 기록하는 방식보다 단순하고 안전하다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `MAX_HISTORY` | 100 단계 |
| `_snapshot(boxes)` | 각 BBox dict 를 복사한 독립 사본 |
| `History(limit=100)` | |
| `.push(boxes)` | 변경 **직전**에 호출. 직전 기록과 똑같으면 쌓지 않고 `False`. 새로 쌓으면 Redo 기록을 비움 |
| `.undo(current)` | 이전 상태 사본을 돌려줌 (현재 상태는 Redo 로). 없으면 `None` |
| `.redo(current)` | Undo 한 것을 다시 적용한 사본. 없으면 `None` |
| `.clear()` | 다른 이미지를 열 때 |
| `.can_undo`, `.can_redo`, `len()` | 버튼 활성화 등에 사용 |

## 의존성

- **사용하는 것**: 없음
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md), [`tests/test_viewport`](../../tests/test_viewport.md)

## 사용 예

```python
self.history.push(self.boxes)        # 바꾸기 직전
self.boxes.append(new_box)

prev = self.history.undo(self.boxes) # Ctrl+Z
if prev is not None:
    self.boxes = prev
```

## 주의사항

- `push` 를 **변경 뒤에** 부르면 한 단계가 밀린다. 반드시 바꾸기 직전에 부른다.
- 기록은 이미지 단위다. 다른 사진으로 넘어가면 `clear()` 되므로 이전 사진의 편집은 되돌릴 수 없다 (이미 저장된 상태).
- 100단계를 넘으면 가장 오래된 기록부터 버린다.
