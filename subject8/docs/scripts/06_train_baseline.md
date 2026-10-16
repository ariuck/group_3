# `subject8/scripts/06_train_baseline.py`

> Baseline 학습. 한 Dataset Version 의 Train 전체로 YOLO11n 을 학습하고, Weight 를 보관하고 학습 조건 기록을 남긴다 (산출물 2). 기본은 공식 Version `kimchi_v5` (Train 558장) → `baseline_v5`.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/06_train_baseline.py)

## 사용법

```bash
cd subject8
python scripts/06_train_baseline.py                       # 공식 Version → baseline_v5
python scripts/06_train_baseline.py --version kimchi_v4   # 지난 Version 재현 → baseline_v4
```

| | 공식 Version (`kimchi_v5`) | 지난 Version (예 `kimchi_v4`) |
|---|---|---|
| 입력 | `configs/dataset.yaml`, `data/yolo/`, `manifests/train.csv`·`val.csv` | `configs/dataset_v4.yaml`, `data/yolo_v4/`, `manifests/kimchi_v4/` |
| 실행 폴더 | `runs/baseline_v5/` | `runs/baseline_v4/` |
| Weight ([`registry`](../src/registry.md)) | `models/baseline/baseline_v5.pt` + 공식 Baseline 이면 `baseline_best.pt` 복사본 | `models/history/kimchi_v4/baseline_v4.pt` |
| 조건 기록 | `reports/02_baseline/baseline_training_condition.md` | `reports/history/kimchi_v4/baseline_v4_training_condition.md` |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `BASELINE` | **Baseline 조건을 정하는 유일한 곳** — `yolo11n.pt`, epochs 50, imgsz 640, batch 16, seed 42, AdamW, lr0 0.001. 개선 실험([`10`](10_train_v2.md) · [`11`](11_train_v5.md) · [`14`](14_train_tiles_v5.md))도 이 값을 불러와 변수 하나만 바꾼다 |
| `DATA_YAML`, `MANIFEST_DIR`, `YOLO_DIR` | `precheck()` 가 보는 폴더. 기본 공식 Version, `main()` 의 `--version` 이나 10·11 이 자기 Version 폴더로 바꾼다 |
| `precheck()` | 학습 전 확인: dataset yaml 존재, `{train,val}` 의 사진·라벨이 manifest 와 **정확히 같은 집합**, Dataset Version 이 하나 |
| `main()` | Weight 가 이미 있으면 멈춤 → precheck → Version 확인 → [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관 → 조건 기록 |

## 핵심 동작

- `precheck` 가 폴더와 manifest 를 대조하므로, Frozen Test·Bridge Holdout 사진이 학습 폴더에 섞여 있으면 학습을 시작하지 않는다.
- 학습 점검(가이드 17.4)이 모두 통과해야 Weight 를 보관한다.
- 조건 기록에는 manifest·Weight 의 sha256 앞 12자리를 남겨, 어떤 목록·Weight 인지 나중에 확인할 수 있다.
- best.pt epoch 의 학습 중 Validation 지표를 **참고**로 적는다. 공식 평가(`baseline_metrics.csv`)는 [`07`](07_evaluate_baseline.md).

## 이력

kimchi_v1 첫 Baseline(`baseline_v1`, 574장) → 실패 분석으로 Dataset 을 v2~v4 로 고치고 v4 에서 다시 학습(`baseline_v4`, 526장) → v4 Val 누수를 없애려 v5 로 다시 나누고 다시 학습(`baseline_v5`, 558장, 공식). 가이드 11.5·20.5 "Baseline 과 Improved 비교기준도 같은 Version 으로". 지난 Version 기록은 `reports/history/<Version>/`.

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행. [`10`](10_train_v2.md) 이 `BASELINE`·`precheck` 를 불러 쓰고, [`11`](11_train_v5.md) 은 10 을 통해 쓴다

## 주의사항

- 실행 폴더나 보관 Weight 가 이미 있으면 멈춘다 (Baseline 은 한 번만, 덮어쓰지 않음).
- `models/` 의 Weight 와 `runs/<실행>/` 의 results.csv·args.yaml·그래프는 Git 에 올라간다 (`weights/` 와 사진 미리보기는 제외).
- RTX 3060 기준 batch 16 에서 GPU 약 2GB, 50 epoch 약 5분.
