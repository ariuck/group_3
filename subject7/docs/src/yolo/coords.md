# `src/yolo/coords.py`

> YOLO 비율값 ↔ 원본 이미지 픽셀 좌표 변환. 화면과 무관한 순수 함수 2개.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/yolo/coords.py)

## 역할

YOLO TXT 한 줄은 `class_id x_center y_center width height` 이고, 좌표는 픽셀이 아니라 **이미지 크기에 대한 0~1 비율**이다. 프로그램 안에서는 BBox 를 원본 픽셀 좌표(왼쪽 위 `x1,y1` / 오른쪽 아래 `x2,y2`)로 다루므로, 읽을 때와 저장할 때 이 변환을 쓴다.

## 주요 구성요소

| 함수 | 입력 | 출력 | 계산 |
|---|---|---|---|
| `yolo_to_pixel(xc, yc, w, h, img_w, img_h)` | 비율값 + 이미지 크기 | `(x1, y1, x2, y2)` | `x1 = (xc - w/2) × img_w` … |
| `pixel_to_yolo(x1, y1, x2, y2, img_w, img_h)` | 픽셀 좌표 + 이미지 크기 | `(xc, yc, w, h)` | `xc = (x1 + x2) / 2 / img_w` … |

두 함수는 서로 정반대 계산이라 왕복해도 값이 유지된다 (4K 기준 소수 9자리 이내).

## 의존성

- **사용하는 것**: 없음
- **사용하는 곳**: [`yolo_loader`](yolo_loader.md), [`yolo_writer`](yolo_writer.md), [`ui/main_window`](../ui/main_window.md) (선택 BBox 의 YOLO 값 표시), [`tests/day1_selftest`](../../tests/day1_selftest.md)

## 사용 예

```python
from src.yolo.coords import yolo_to_pixel, pixel_to_yolo

x1, y1, x2, y2 = yolo_to_pixel(0.5, 0.5, 0.1, 0.1, 3840, 2160)   # (1728.0, 972.0, 2112.0, 1188.0)
pixel_to_yolo(x1, y1, x2, y2, 3840, 2160)                          # (0.5, 0.5, 0.1, 0.1)
```

## 주의사항

- 이미지 왼쪽 위가 `(0, 0)` 이고 오른쪽·아래로 갈수록 값이 커진다.
- 범위 검사(0~1)는 하지 않는다. 범위 밖 값은 [`validator`](../validation/validator.md) 가 찾는다.
