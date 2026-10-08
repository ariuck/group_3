"""YOLO 비율값 ↔ 원본 이미지 픽셀 좌표 변환 (화면(Tkinter)과 무관한 순수 함수).

YOLO TXT 한 줄 = 객체 하나:   class_id  x_center  y_center  width  height
  ※ 좌표는 "픽셀"이 아니라 "이미지 크기에 대한 비율(0~1)" 이다.
  ※ 이미지 왼쪽 위가 (0, 0), 오른쪽으로 갈수록 x 증가, 아래로 갈수록 y 증가.
"""


def yolo_to_pixel(xc, yc, w, h, img_w, img_h):
    """YOLO 비율값(중심 + 크기) → 원본 이미지 픽셀 좌표 (왼쪽위 x1,y1 / 오른쪽아래 x2,y2)."""
    return ((xc - w / 2) * img_w, (yc - h / 2) * img_h,
            (xc + w / 2) * img_w, (yc + h / 2) * img_h)


def pixel_to_yolo(x1, y1, x2, y2, img_w, img_h):
    """원본 이미지 픽셀 좌표 → YOLO 비율값(중심 + 크기). yolo_to_pixel 의 정반대 계산."""
    return ((x1 + x2) / 2 / img_w, (y1 + y2) / 2 / img_h, (x2 - x1) / img_w, (y2 - y1) / img_h)
