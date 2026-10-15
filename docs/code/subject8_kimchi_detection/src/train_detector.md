# `subject8_kimchi_detection/src/train_detector.py`

> YOLO11 학습 공통 기능. Smoke Test · Baseline · 7일차 개선 실험이 모두 같은 `train_detector()` 를 써서 "바꾼 변수 하나" 외에는 학습 방식이 같다는 것을 보장한다. 학습 점검·Weight 보관·조건 기록도 함께 한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/src/train_detector.py)

## 역할

- 가이드 17.2 "재사용 가능한 학습 함수" 구현.
- 가이드 17.4 학습 중 확인 항목(중단 없음, NaN 없음, 매 epoch Validation, best.pt·results.csv 생성)을 자동 점검.
- 가이드 17.1 학습 조건 기록 항목(Model, Dataset Version, Manifest, Epoch, Batch, Image Size, Seed, Optimizer, LR, GPU, Ultralytics 버전, 시작·종료 시간)을 Markdown 으로 남김.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `train_detector(model_name, data_yaml, epochs, imgsz, batch, seed, project, name, optimizer="AdamW", lr0=0.001, workers=8, patience=100, **extra)` | YOLO 학습 1회. `deterministic=True`, `exist_ok=False`. **같은 이름의 실행 폴더가 있으면 `FileExistsError`** (Ultralytics 가 이름을 `baseline_v12` 처럼 바꿔 저장하는 것을 막음). 반환: `save_dir, best, last, results_csv, start, end, seconds, optimizer, lr0, device, gpu` |
| `check_training(result)` | `{항목: (통과, 설명)}` — best.pt·last.pt·results.csv 생성, 모든 epoch 에 mAP50 기록, Loss NaN/inf 없음 |
| `best_epoch_metrics(results_csv)` | mAP50-95 가 가장 높은 epoch(= best.pt)의 학습 중 Validation P·R·mAP50·mAP50-95. **참고용**, 공식 평가는 5일차 |
| `copy_weight(src, dest)` | `runs/.../best.pt` → `models/baseline/baseline_best.pt` 처럼 역할이 보이는 이름으로 복사. 이미 있으면 덮어쓰지 않고 멈춤 |
| `write_condition_report(path, title, condition, result, checks, notes)` | 학습 조건 · 실행 환경(PC 이름·OS·CPU·RAM·GPU 와 드라이버·GPU 최대 메모리·Python/Ultralytics/PyTorch 버전·시간) · 점검 결과 Markdown |
| `machine_info()` | 학습한 PC 정보 `host, os, cpu, ram, driver, python` (`/etc/os-release`, `/proc/cpuinfo`, `/proc/meminfo`, `nvidia-smi`). 못 읽으면 `-`. 팀원이 각자 PC 에서 실험해도 어느 PC 결과인지 구분하기 위함 |
| `rel(path)` | 기록용 상대경로 (현재 폴더 = 프로젝트 루트 기준). 다른 PC 에서도 같은 기록이 되도록 |
| `sha256_short(path)` | manifest·Weight 지문 12자리 (어떤 파일로 학습했는지 확인용) |
| `pick_device()`, `versions()` | GPU 선택, Ultralytics·PyTorch·CUDA 버전 |

## 의존성

- **사용하는 것**: `ultralytics.YOLO`, `torch`
- **사용하는 곳**: [`scripts/05_smoke_train`](../scripts/05_smoke_train.md), [`scripts/06_train_baseline`](../scripts/06_train_baseline.md), [`scripts/10_train_v2`](../scripts/10_train_v2.md)

## 핵심 동작

```python
result = train_detector(model_name="yolo11n.pt", data_yaml="configs/dataset.yaml",
                        epochs=50, imgsz=640, batch=16, seed=42, project="runs", name="baseline_v1")
checks = check_training(result)
```

## 주의사항

- **Optimizer 를 `auto` 가 아니라 `AdamW` 로 고정**했다. Ultralytics 의 `auto` 는 학습 반복 수에 따라 SGD/AdamW 를 스스로 고르므로, 7일차에 Epoch·Batch 를 바꾸면 Optimizer 까지 같이 바뀌어 "한 변수만 변경" 원칙이 깨질 수 있다.
- Ultralytics 8.4 의 best.pt 기준은 mAP50-95 단독이다 (fitness 가중치 `[0, 0, 0, 1]`). 버전이 바뀌면 `best_epoch_metrics` 도 확인한다.
- `cache` 는 쓰지 않는다. `ram` 은 결과가 비결정적일 수 있다는 경고가 있고, `disk` 는 4K 원본을 그대로 `.npy` 로 저장해 수십 GB 를 쓴다.
- `data_yaml` 의 상대 `path:` 는 현재 폴더 기준이므로, 호출하는 스크립트는 먼저 프로젝트 루트로 `os.chdir` 한다.
