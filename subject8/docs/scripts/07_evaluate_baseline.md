# `subject8/scripts/07_evaluate_baseline.py`

> Baseline Validation 평가. 공식 Baseline `models/baseline/baseline_best.pt` 를 그 Dataset Version 의 Validation 에서 평가해 `reports/02_baseline/baseline_metrics.csv`(산출물 2)와 Class 별 성능, 그래프(산출물 5)를 남긴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/07_evaluate_baseline.py)

## 사용법

```bash
cd subject8
python scripts/07_evaluate_baseline.py
```

어느 실행이 공식 Baseline 인지는 [`src/registry`](../src/registry.md) 의 `OFFICIAL["baseline"]` (지금 `baseline_v5` · `kimchi_v5` · 640). 공식을 바꾸면 이 스크립트도 따라간다.

| 입력 | 출력 |
|---|---|
| `models/baseline/baseline_best.pt`, `runs/<공식 Baseline>/args.yaml`(학습 조건), 그 Version 의 dataset yaml | `reports/02_baseline/baseline_metrics.csv`, `reports/02_baseline/baseline_class_metrics.csv`, `reports/figures/baseline/baseline_{results, confusion_matrix, confusion_matrix_normalized, pr_curve}.png`, `runs/eval/<실행>_val/` |

지난 Version 의 Baseline 평가 결과는 `reports/history/<Version>/` 에 있다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `WEIGHT`, `MODEL_VERSION` | `registry.resolve("baseline")` — (Weight 경로, 실행 이름) |
| `DATASET_VERSION`, `DATA_YAML` | 실행 이름의 `_v<N>` → Version → 그 Version 의 dataset yaml |
| `main()` | 학습 때 `args.yaml` 의 imgsz·batch 로 [`evaluate_detector`](../src/evaluate_detector.md)(split=`val`) → CSV 2개 → 그래프 복사 → 콘솔 표 |

### `baseline_metrics.csv` 칸

`model_version, dataset_version, split, imgsz, batch, epochs, seed, images, instances, precision, recall, map50, map50_95` (가이드 산출물 예시 칸 + 사진·정답 수)

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/evaluate_detector`](../src/evaluate_detector.md), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md) (`rel`)
- **사용하는 곳**: 직접 실행 (교과 8 5일차)

## 주의사항

- Frozen Test 는 쓰지 않는다 (`split="val"` 고정).
- 그래프는 사진이 들어가지 않는 것만 `reports/figures/` 로 복사한다. `val_batch*_pred.jpg` 처럼 사진이 보이는 파일은 `runs/` 에만 둔다 (Git 제외).
- 다시 실행하면 CSV·그래프를 덮어쓴다. Weight 가 같으면 결과도 같다.
