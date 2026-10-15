# `src/bbox/bbox_edit.py`

> 기존 BBox 이동·크기 조절 계산. 8개 핸들의 위치·판정과 새 좌표 계산을 담당하는 순수 함수 모음.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/bbox/bbox_edit.py)

## 역할

- 선택된 BBox 의 핸들 8개 위치를 구하고, 마우스가 어느 핸들 위에 있는지 판정한다.
- 이동·크기 조절 결과를 **새 dict 사본**으로 돌려준다. 원래 dict 를 고치지 않으므로 드래그 중 `Esc` 로 취소하면 원래 값이 그대로 남는다.

```
nw ── n ── ne
│          │
w          e
│          │
sw ── s ── se
```

## 주요 구성요소

| 이름 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `HANDLE_NAMES` | – | 8개 이름 | 시계 방향 `nw, n, ne, e, se, s, sw, w` |
| `HANDLE_CURSORS` | – | `{핸들: Tk 커서}` | X11/WSL 에서 쓸 수 있는 커서 이름 (`top_left_corner`, `sb_v_double_arrow` 등) |
| `handle_points(box)` | BBox | `{이름: (x, y)}` | 원본 픽셀 좌표 |
| `hit_handle(box, x, y, tol)` | BBox, 좌표, 허용 거리 | 이름 또는 `None` | 체비셰프 거리(`max(|dx|,|dy|)`) ≤ tol 인 것 중 **가장 가까운** 핸들 |
| `move_box(box, dx, dy, img_w, img_h)` | BBox, 이동량 | 새 BBox | 크기 유지, 이미지 밖으로 못 나감 |
| `resize_box(box, handle, x, y, img_w, img_h, min_size=4)` | BBox, 핸들, 마우스 위치 | 새 BBox | 끄는 변만 움직이고 반대쪽 변 고정, 최소 `min_size`, 이미지 안으로 보정 |

## 의존성

- **사용하는 것**: [`bbox_manager`](bbox_manager.md) (`MIN_BOX_PX`, `clamp`)
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md), [`tests/test_bbox_edit`](../../tests/test_bbox_edit.md)

## 사용 예

```python
from src.bbox.bbox_edit import hit_handle, resize_box, move_box

h = hit_handle(box, mx, my, tol=8 / viewport.scale)   # 화면 8px 를 원본 픽셀로 환산해서 넘긴다
if h:
    new = resize_box(box, h, mx, my, img_w, img_h)
else:
    new = move_box(box, dx, dy, img_w, img_h)
```

## 주의사항

- `tol` 은 **원본 픽셀** 단위다. 화면 배율과 관계없이 일정한 크기로 잡히게 하려면 호출 쪽에서 화면 px ÷ 배율로 넘긴다.
- 이미지 가장자리에 붙은 작은 BBox 를 키우면 반대쪽이 밖으로 나갈 수 있어서 `resize_box` 가 한 번 더 안으로 넣는다. 그래서 핸들을 이미지 밖까지 끌어도 BBox 는 경계에서 멈춘다.
