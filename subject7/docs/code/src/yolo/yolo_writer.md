# `src/yolo/yolo_writer.py`

> YOLO TXT 저장. BBox 목록(원본 픽셀 좌표)을 YOLO 비율값 TXT 로 쓴다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/yolo/yolo_writer.py)

## 역할

- 화면에서 편집한 BBox 를 WORK 폴더에 YOLO 형식으로 저장한다.
- 저장할 폴더가 없으면 만든다.

## 주요 구성요소

| 함수 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `write_yolo_file(txt_path, boxes, img_w, img_h)` | 경로, BBox 목록, 이미지 크기 | – | 한 줄에 `cls xc yc w h` (소수 10자리), 줄바꿈 `\n`, UTF-8. BBox 가 0개면 **빈 파일** |

## 의존성

- **사용하는 것**: [`coords.pixel_to_yolo`](coords.md)
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md) (저장)

## 사용 예

```python
from src.yolo.yolo_writer import write_yolo_file
from src.data_paths import work_label_path

write_yolo_file(work_label_path(img), [{"cls": 2, "x1": 100, "y1": 50, "x2": 300, "y2": 200}], 3840, 2160)
```

## 주의사항

- **RAW 보호 검사는 이 함수에 없다.** 경로가 RAW 안인지는 호출하는 쪽([`main_window`](../ui/main_window.md) 이 [`is_inside`](../data_paths.md) 로)에서 막는다.
- 임시 파일 → 교체 방식이 아니라 바로 덮어쓴다. 저장 도중 프로그램이 죽으면 그 TXT 가 비거나 잘릴 수 있다. ([`manifest_writer._save`](../manifest/manifest_writer.md) 는 원자적 저장을 한다)
- 모든 BBox 의 좌표를 다시 계산해서 쓰므로, 손대지 않은 BBox 도 원본 TXT 와 마지막 자리 숫자가 다를 수 있다. 비교는 반올림 서명([`label_signature`](yolo_loader.md))으로 한다.
