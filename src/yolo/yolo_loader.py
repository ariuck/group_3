"""YOLO TXT 불러오기 — 같은 이름의 TXT 를 찾고, BBox 목록(원본 픽셀 좌표)으로 만든다."""
from pathlib import Path

from src.yolo.coords import yolo_to_pixel


def find_raw_label(image_path):
    """이미지와 '같은 이름'의 원본 TXT 를 찾는다. 못 찾으면 None.

    회사 데이터는  .../images/train/a.jpg  ↔  .../labels/train/a.txt  구조이므로
    경로 중 'images' 를 'labels' 로 바꿔서 찾고, 없으면 이미지와 같은 폴더도 확인한다.
    """
    image_path = Path(image_path)
    candidates = []
    parts = list(image_path.parts)
    if "images" in parts:
        i = len(parts) - 1 - parts[::-1].index("images")      # 마지막에 나오는 'images' 를 교체
        parts[i] = "labels"
        candidates.append(Path(*parts).with_suffix(".txt"))
    candidates.append(image_path.with_suffix(".txt"))
    for c in candidates:
        if c.is_file():
            return c
    return None


def read_yolo_file(txt_path, img_w, img_h):
    """TXT 를 읽어 BBox 목록(원본 픽셀 좌표)으로 만든다.

    반환: (boxes, bad_lines)
      boxes     = [{"cls": 2, "x1":.., "y1":.., "x2":.., "y2":..}, ...]
      bad_lines = 형식이 잘못되어 읽지 못한 줄 수  (몰래 버리지 않고 사용자에게 알려 주기 위함)
    ※ TXT 가 비어 있으면 boxes 도 빈 목록이다. 이건 '오류'가 아니라 '정상 김치(이물 없음)'일 수 있다.
    """
    boxes, bad_lines = [], 0
    for line in Path(txt_path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        try:
            if len(parts) != 5:
                raise ValueError("필드가 5개가 아님")
            cls = int(parts[0])
            xc, yc, w, h = (float(p) for p in parts[1:])
        except ValueError:
            bad_lines += 1                     # 형식 오류: 개수만 세어 두고 계속 진행
            continue
        x1, y1, x2, y2 = yolo_to_pixel(xc, yc, w, h, img_w, img_h)
        boxes.append({"cls": cls, "x1": x1, "y1": y1, "x2": x2, "y2": y2})
    return boxes, bad_lines


def read_yolo_rows(txt_path):
    """TXT 를 (class, x_center, y_center, width, height) 목록으로 읽는다 (좌표 변환 없음).
    읽을 수 없는 줄은 건너뛰고, 파일이 없으면 빈 목록."""
    p = Path(txt_path) if txt_path else None
    if p is None or not p.is_file():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        try:
            if len(parts) != 5:
                raise ValueError
            rows.append((int(parts[0]), *(float(v) for v in parts[1:])))
        except ValueError:
            continue
    return rows


def label_signature(txt_path, digits=5):
    """두 TXT 가 같은 내용인지 비교하기 위한 값 (소수 오차를 무시하도록 반올림 + 정렬)."""
    return sorted((c, *(round(v, digits) for v in vals)) for c, *vals in read_yolo_rows(txt_path))
