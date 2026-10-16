# `subject8/scripts/07_evaluate_baseline.py`

> Baseline Validation 평가. 공식 Baseline `baseline_best.pt` (`baseline_v4`, kimchi_v4 · 640) 를 Validation 132장에서 평가해 `reports/02_baseline/baseline_metrics.csv`(산출물 2)와 Class 별 성능, 그래프(산출물 5)를 남긴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/07_evaluate_baseline.py)

## 사용법

```bash
cd subject8
python scripts/07_evaluate_baseline.py
```

| 입력 | 출력 |
|---|---|
| `models/baseline/baseline_best.pt`, `runs/baseline_v4/args.yaml`(학습 조건), `configs/dataset.yaml`, `manifests/val.csv`(Dataset Version) | `reports/02_baseline/baseline_metrics.csv`, `reports/02_baseline/baseline_class_metrics.csv`, `reports/figures/baseline/baseline_{results, confusion_matrix, confusion_matrix_normalized, pr_curve}.png`, `runs/eval/baseline_v4_val/` |

이력: kimchi_v1 첫 Baseline 의 결과는 `reports/history/baseline_v1_metrics.csv`·`baseline_v1_class_metrics.csv`, 그래프 `reports/figures/history/baseline_v1_*.png` 로 이름을 바꿔 보관한다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `MODEL_VERSION` | `baseline_v4` |
| `main()` | 학습 때 `args.yaml` 의 imgsz·batch 로 [`evaluate_detector`](../src/evaluate_detector.md)(split=`val`) → CSV 2개 → 그래프 복사 → 콘솔 표 |

### `baseline_metrics.csv` 칸

`model_version, dataset_version, split, imgsz, batch, epochs, seed, images, instances, precision, recall, map50, map50_95` (가이드 산출물 예시 칸 + 사진·정답 수)

## 의존성

- **사용하는 것**: [`src/evaluate_detector`](../src/evaluate_detector.md), [`src/train_detector`](../src/train_detector.md) (`rel`), `PyYAML`
- **사용하는 곳**: 직접 실행 (교과 8 5일차)

## 주의사항

- Frozen Test 는 쓰지 않는다 (`split="val"` 고정).
- 그래프는 사진이 들어가지 않는 것만 `reports/figures/` 로 복사한다 (Git 에 올라감). `val_batch*_pred.jpg` 처럼 사진이 보이는 파일은 `runs/` 에만 둔다.
- 다시 실행하면 CSV·그래프를 덮어쓴다. Weight 가 같으면 결과도 같다.
