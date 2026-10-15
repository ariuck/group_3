# `subject8/scripts/05_smoke_train.py`

> 3일차 Smoke Test. 작은 데이터로 학습 → Weight → 이미지 Prediction 이 끝까지 되는지 확인하고 `reports/history/smoke_test.md` 를 남긴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../scripts/05_smoke_train.py)

## 사용법

```bash
cd subject8
python scripts/05_smoke_train.py              # 3 epoch, imgsz 640, batch 16
python scripts/05_smoke_train.py --overwrite  # runs/smoke_v1 을 지우고 다시
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--epochs` | 3 | |
| `--imgsz` | 640 | |
| `--batch` | 16 | Baseline 과 같은 값으로 GPU 메모리(OOM) 확인 |
| `--name` | `smoke_v1` | `runs/<name>` |
| `--overwrite` | 끔 | 같은 이름의 실행 폴더와 예측 폴더를 지우고 다시 |

| 입력 | 출력 |
|---|---|
| `data/yolo/` (03 `--copy-files` 결과), `configs/dataset.yaml` | `data/smoke/`, `configs/smoke_dataset.yaml`, `runs/smoke_v1/`, `runs/smoke_v1_predict/`, `reports/history/smoke_test.md` |

## 핵심 동작

1. [`build_smoke_dataset`](../src/smoke_dataset.md) → Train 40 / Val 8
2. [`train_detector`](../src/train_detector.md) 로 3 epoch 학습 → [`check_training`](../src/train_detector.md) 점검
3. Smoke Val 첫 사진 1장 Prediction. 3 epoch 모델은 확신이 낮아 conf 0.25 에서 0개일 수 있어, 0개면 conf 0.01 로 다시 예측해 **BBox·Class·Confidence 표시 기능**을 확인한다
4. 점검 7항목을 콘솔과 `reports/history/smoke_test.md` 에 기록. 하나라도 실패하면 종료 코드 1

## 의존성

- **사용하는 것**: [`src/smoke_dataset`](../src/smoke_dataset.md), [`src/train_detector`](../src/train_detector.md), `ultralytics.YOLO`
- **사용하는 곳**: 직접 실행 (교과 8 3일차)

## 주의사항

- Smoke Weight 는 Baseline 이 아니다. 성능 숫자로 판단하지 않는다.
- 시작할 때 프로젝트 루트로 `os.chdir` 한다 (`dataset.yaml` 의 상대 `path:` 기준).
