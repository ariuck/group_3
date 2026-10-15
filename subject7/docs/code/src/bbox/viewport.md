# `src/bbox/viewport.py`

> 확대(Zoom)·이동(Pan) 좌표 계산. 캔버스 좌표 ↔ 이미지 픽셀 좌표 변환만 담당하며 tkinter 에 의존하지 않는다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/bbox/viewport.py)

## 역할

```
canvas = image × scale + offset
image  = (canvas − offset) ÷ scale
```

BBox 는 항상 **이미지 픽셀 좌표**로 저장하고, 그릴 때만 캔버스 좌표로 바꾼다. 그래서 확대 배율이 바뀌어도 저장되는 YOLO 좌표가 흔들리지 않는다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `MIN_SCALE` / `MAX_SCALE` | 0.1 (10%) / 20.0 (2000%) |
| `ZOOM_STEP` | 1.25 — 휠 한 칸·버튼 한 번에 곱하는 배율 |
| `Viewport(scale, offset_x, offset_y)` | |
| `.image_to_canvas(x, y)` / `.canvas_to_image(cx, cy)` | 점 변환 |
| `.box_to_canvas(box)` | BBox → `(cx1, cy1, cx2, cy2)` |
| `.canvas_to_image_clamped(cx, cy, img_w, img_h)` | 마우스 위치를 이미지 좌표로 바꾸고 이미지 범위 안으로 자름 |
| `.zoom_at(factor, cx, cy)` | **커서 아래 지점을 고정**한 채 배율 변경. 실제로 바뀌었으면 `True` (최소·최대에 닿으면 `False`) |
| `.zoom_in(cx, cy)` / `.zoom_out(cx, cy)` | `ZOOM_STEP` 으로 확대 / 축소 |
| `.zoom_percent` | 정수 % (화면 표시용) |
| `.pan(dx, dy)` | 캔버스 기준 이동 |
| `.fit(img_w, img_h, canvas_w, canvas_h, margin=0, upscale=False)` | 전체가 보이게 배율을 정하고 가운데 정렬. `upscale=False` 면 최대 100% |
| `.reset()` | 배율 1, 원점 0 |

## 의존성

- **사용하는 것**: 없음
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md), [`tests/test_viewport`](../../tests/test_viewport.md)

## 사용 예

```python
from src.bbox.viewport import Viewport

vp = Viewport()
vp.fit(3840, 2160, 1200, 700)           # 약 31%
vp.zoom_at(1.25, 600, 350)              # 화면 가운데를 기준으로 확대
x, y = vp.canvas_to_image(event.x, event.y)
```

## 주의사항

- `fit` 은 이미지나 캔버스 크기가 0 이하이면 `reset()` 한다 (창이 아직 그려지지 않은 순간 대비).
- 이 모듈의 `_clamp` 는 [`bbox_manager.clamp`](bbox_manager.md) 와 같은 동작의 별도 함수다.
