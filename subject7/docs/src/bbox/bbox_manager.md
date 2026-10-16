# `src/bbox/bbox_manager.py`

> BBox 생성·선택·이상 검사. 화면(Tkinter)과 무관한 순수 함수이며, 좌표는 항상 원본 이미지 픽셀 기준이다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/bbox/bbox_manager.py)

## 역할

- 드래그한 두 점으로 BBox 를 만든다 (이미지 밖은 잘라내고, 너무 작으면 만들지 않음).
- 클릭한 위치의 BBox 를 고른다 (겹치면 안쪽의 작은 것).
- 원본 라벨의 이상한 BBox 를 **고치지 않고** 문장으로 알려 준다 (라벨 목록의 빨간 `⚠ 확인`).

BBox 형식: `{"cls": 2, "x1": .., "y1": .., "x2": .., "y2": ..}`

## 주요 구성요소

| 이름 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `MIN_DRAG_PX` | – | 5 | 화면에서 이보다 짧은 드래그는 실수로 보고 BBox 를 만들지 않음 (UI 에서 사용) |
| `MIN_BOX_PX` | – | 4 | 원본 기준 최소 BBox 가로·세로 |
| `clamp(v, lo, hi)` | 숫자 | 숫자 | 범위 안으로 가둠 |
| `make_box(cls, ax, ay, bx, by, img_w, img_h)` | 두 점 + 이미지 크기 | BBox 또는 `None` | ① 이미지 밖 잘라냄 ② 좌상단·우하단 정렬 ③ 4px 미만이면 `None` |
| `find_box_at(boxes, x, y)` | BBox 목록, 원본 좌표 | 번호 또는 `None` | 점을 포함하는 BBox 중 **면적이 가장 작은 것** (같으면 뒤의 것) |
| `box_problems(box, img_w, img_h, n_classes=7, unused=())` | BBox | `list[str]` | Class 범위 밖 / 사용 안 하는 Class / 이미지 밖(0.5px 허용) / 4px 미만. 비어 있으면 정상 |

## 의존성

- **사용하는 것**: 없음
- **사용하는 곳**: [`bbox_edit`](bbox_edit.md) (`MIN_BOX_PX`, `clamp`), [`ui/main_window`](../ui/main_window.md), [`tests/day1_selftest`](../../tests/day1_selftest.md), [`tests/test_box_problems`](../../tests/test_box_problems.md), [`tests/test_bbox_edit`](../../tests/test_bbox_edit.md)

## 사용 예

```python
from src.bbox.bbox_manager import make_box, find_box_at, box_problems

b = make_box(2, 300, 200, 100, 50, 3840, 2160)   # {'cls': 2, 'x1': 100, 'y1': 50, 'x2': 300, 'y2': 200}
find_box_at([b], 150, 100)                       # 0
box_problems({"cls": 4, **{k: b[k] for k in "x1 y1 x2 y2".split()}}, 3840, 2160, unused={4})
# ['Class 4 는 이번 프로젝트에서 사용하지 않는 번호']
```

## 주의사항

- `box_problems` 의 `n_classes` 기본값은 7 이다. UI 는 `len(settings.CLASSES)` 와 `settings.UNUSED_CLASSES` 를 넘겨서 쓴다.
- 이 모듈은 Class 4 로 BBox 를 만드는 것을 막지 않는다. 막는 것은 UI 의 몫이다.
