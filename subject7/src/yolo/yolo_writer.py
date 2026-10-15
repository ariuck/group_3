"""YOLO TXT 저장 — BBox 목록(원본 픽셀 좌표)을 YOLO 비율값 TXT 로 저장한다."""
from pathlib import Path

from src.yolo.coords import pixel_to_yolo


def write_yolo_file(txt_path, boxes, img_w, img_h):
    """BBox 목록(원본 픽셀 좌표) → YOLO TXT 로 저장.  BBox 가 0개면 빈 파일이 저장된다."""
    lines = []
    for b in boxes:
        xc, yc, w, h = pixel_to_yolo(b["x1"], b["y1"], b["x2"], b["y2"], img_w, img_h)
        lines.append(f"{b['cls']} {xc:.10f} {yc:.10f} {w:.10f} {h:.10f}")
    txt_path = Path(txt_path)
    txt_path.parent.mkdir(parents=True, exist_ok=True)       # WORK 안의 폴더가 없으면 만든다
    txt_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
