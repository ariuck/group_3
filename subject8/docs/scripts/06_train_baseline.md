# `subject8/scripts/06_train_baseline.py`

> 공식 Baseline 학습. 확정된 Dataset Version `kimchi_v4` 의 Train 전체(526장)로 YOLO11n 을 학습하고, Weight 를 `models/baseline/baseline_best.pt` 로 보관하고 `reports/baseline_training_condition.md` 를 남긴다 (산출물 2).

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/06_train_baseline.py)

## 사용법

```bash
cd subject8
python scripts/06_train_baseline.py
```

| 입력 | 출력 |
|---|---|
| `configs/dataset.yaml`, `data/yolo/{images,labels}/{train,val}`, `manifests/train.csv`·`val.csv` | `runs/baseline_v4/` (results.csv, args.yaml, weights …), `models/baseline/baseline_best.pt`, `reports/baseline_training_condition.md` |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `BASELINE` | **Baseline 조건을 정하는 유일한 곳** — `yolo11n.pt`, epochs 50, imgsz 640, batch 16, seed 42, AdamW, lr0 0.001. 개선 실험([`10_train_v2`](10_train_v2.md))도 이 값을 불러와 변수 하나만 바꾼다 |
| `DATASET_VERSION` | `kimchi_v4` — `data/yolo` 가 이 Version 이 아니면 학습하지 않는다 |
| `RUN_NAME` | `baseline_v4` |
| `precheck()` | 학습 전 확인: `dataset.yaml` 존재, `data/yolo/{train,val}` 의 사진·라벨이 `manifests/{train,val}.csv` 와 **정확히 같은 집합**, Dataset Version 이 하나 |
| `main()` | precheck → Version 확인 → [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관 → 조건 기록 |

## 핵심 동작

- `precheck` 가 폴더와 manifest 를 대조하므로, Frozen Test·Bridge Holdout 사진이 학습 폴더에 섞여 있으면 학습을 시작하지 않는다.
- 학습 점검(가이드 17.4)이 모두 통과해야 Weight 를 `models/baseline/` 로 복사한다.
- 조건 기록에는 manifest 의 sha256 앞 12자리를 남겨, 어떤 목록으로 학습했는지 나중에 확인할 수 있다.
- best.pt epoch 의 학습 중 Validation 지표를 **참고**로 적는다. 공식 평가(`baseline_metrics.csv`)는 [`07`](07_evaluate_baseline.md).

## 이력

kimchi_v1 의 첫 Baseline(`baseline_v1`, 574장 · 640)은 `runs/baseline_v1/`, `models/baseline/baseline_v1_best.pt`, `reports/history/baseline_v1_training_condition.md` 로 보관한다. 그 실패 분석(`reports/failure_hypothesis.md`)으로 Dataset 을 v2~v4 로 고쳤고, 가이드 11.5·20.5("Baseline 과 Improved 비교기준도 같은 Version 으로") 에 따라 v4 에서 Baseline 을 다시 학습했다 (2026-10-14).

## 의존성

- **사용하는 것**: [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행. [`10_train_v2`](10_train_v2.md) 가 `BASELINE`·`precheck` 를 불러 쓴다

## 주의사항

- `runs/baseline_v4` 나 `models/baseline/baseline_best.pt` 가 이미 있으면 멈춘다 (Baseline 은 한 번만, 덮어쓰지 않음). 다시 학습하려면 이전 결과를 직접 옮기거나 지운다.
- `models/` 의 `.pt` 는 `.gitignore` 로 Git 에 올라가지 않는다. `runs/<실행>/results.csv`·`args.yaml` 은 올라간다.
- RTX 3060 기준 batch 16 에서 GPU 약 2GB (Smoke Test 측정), 50 epoch 약 5분.
