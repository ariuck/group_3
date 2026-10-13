# `subject8_kimchi_detection/scripts/01_check_environment.py`

> 교과 8 학습 환경 점검. Python · PyTorch · Ultralytics 버전과 CUDA(GPU) 사용 가능 여부를 출력하고, YOLO11n 사전학습 가중치를 불러와 본다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/scripts/01_check_environment.py)

## 사용법

```bash
cd subject8_kimchi_detection
python scripts/01_check_environment.py
```

출력 예:

```
Python: 3.x
PyTorch: 2.x
Ultralytics: 8.x
CUDA available: True
GPU: <GPU 이름>
YOLO11n loaded successfully!
COCO Classes count: 80
```

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `main()` | 버전·CUDA 출력, GPU 가 있으면 이름 출력, `YOLO('yolo11n.pt')` 로드 시도 (실패해도 오류 메시지만 출력) |

## 의존성

- **사용하는 것**: `torch`, `ultralytics`, 가중치 파일 `yolo11n.pt` (subject8 폴더에 있음. 없으면 Ultralytics 가 내려받으려고 시도)
- **사용하는 곳**: 직접 실행 (교과 8 1일차 환경 점검)

## 주의사항

- `yolo11n.pt` 는 **현재 작업 폴더 기준**으로 찾는다. `subject8_kimchi_detection/` 안에서 실행해야 저장소의 가중치를 쓴다.
- `*.pt` 는 저장소 루트 `.gitignore` 대상이다.
