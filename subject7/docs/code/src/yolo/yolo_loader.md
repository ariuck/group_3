# `src/yolo/yolo_loader.py`

> YOLO TXT 불러오기. 이미지와 같은 이름의 원본 TXT 를 찾고, BBox 목록(원본 픽셀 좌표)이나 비율값 행 목록으로 읽는다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/yolo/yolo_loader.py)

## 역할

- `.../images/train/a.jpg` ↔ `.../labels/train/a.txt` 짝을 찾는다.
- 형식이 잘못된 줄은 **몰래 버리지 않고 개수를 센다** (화면에서 경고하기 위해).
- 두 TXT 가 같은 내용인지 비교하는 서명(`label_signature`)을 만든다. 검수표의 "원본에서 바뀌었나" 판단에 쓴다.

## 주요 구성요소

| 함수 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `find_raw_label(image_path)` | 이미지 경로 | `Path` 또는 `None` | 경로의 **마지막** `images` 를 `labels` 로 바꿔 찾고, 없으면 이미지와 같은 폴더를 본다 |
| `parse_class_id(text)` | `'2'`, `'2.0'` | `int` | 정수로 떨어지는 실수는 받아 주고 `'2.5'` 는 `ValueError` |
| `read_yolo_file(txt, img_w, img_h)` | TXT, 이미지 크기 | `(boxes, bad_lines)` | `boxes = [{"cls","x1","y1","x2","y2"}]` (픽셀), `bad_lines` = 읽지 못한 줄 수 |
| `read_yolo_rows(txt)` | TXT 또는 `None` | `[(cls, xc, yc, w, h)]` | 좌표 변환 없이 읽음. 잘못된 줄은 건너뜀, 파일이 없으면 `[]` |
| `label_signature(txt, digits=5)` | TXT | 정렬된 튜플 목록 | 소수 5자리 반올림 + 정렬. 줄 순서나 미세한 반올림 차이는 "같음"으로 본다 |

## 의존성

- **사용하는 것**: [`coords.yolo_to_pixel`](coords.md)
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md) (`find_raw_label`, `read_yolo_file`), [`manifest/manifest_writer`](../manifest/manifest_writer.md) (`read_yolo_rows`, `label_signature`), [`tests/test_label_io`](../../tests/test_label_io.md), [`tests/day1_selftest`](../../tests/day1_selftest.md)

## 사용 예

```python
from src.yolo.yolo_loader import find_raw_label, read_yolo_file, label_signature

txt = find_raw_label("data/raw/DS1/images/train/a.jpg")     # data/raw/DS1/labels/train/a.txt
boxes, bad = read_yolo_file(txt, 3840, 2160)
changed = label_signature(work_txt) != label_signature(txt)
```

## 주의사항

- **빈 TXT 는 오류가 아니다.** 이물이 없는 정상 김치일 수 있으므로 `boxes = []` 로 정상 반환한다.
- 읽을 때 `utf-8-sig` 를 쓴다. Windows 메모장이 붙이는 BOM 이 첫 줄에 섞여도 첫 BBox 를 잃지 않는다.
- Class 번호 해석이 [`validator.parse_label_file`](../validation/validator.md) 와 다르다. 여기서는 `2.0` 을 Class 2 로 읽지만, validator 는 `int()` 만 써서 같은 줄을 `BAD_NUMBER` 로 보고한다.
