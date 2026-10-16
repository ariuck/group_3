# `subject8/scripts/11_train_v5.py`

> `kimchi_v5`(C안 재분할) 학습 — [`06`](06_train_baseline.md) Baseline 조건과 [`10`](10_train_v2.md) 의 해상도 실험(exp001·exp002)을 v5 데이터에서 다시 한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/11_train_v5.py)

## 사용법

```bash
cd subject8
python scripts/03_build_split.py --version kimchi_v5 --copy-files   # 먼저 data/yolo_v5 만들기
python scripts/11_train_v5.py                 # baseline → exp001 → exp002 차례로
python scripts/11_train_v5.py --run exp001    # 하나만
```

| `--run` | 조건 (06 에서 바꾸는 값) | 출력 |
|---|---|---|
| `baseline` | 그대로 (imgsz 640) | `runs/baseline_v5/`, `models/baseline/baseline_v5_best.pt` |
| `exp001` | imgsz 1280 | `runs/exp001_v5_imgsz1280/`, `models/improved/exp001_v5_best.pt` |
| `exp002` | imgsz 1920 · batch 6 | `runs/exp002_v5_imgsz1920/`, `models/improved/exp002_v5_best.pt` |

조건 기록: `reports/06_kimchi_v5/<실행>_training_condition.md`. 입력: `configs/dataset_v5.yaml`, `data/yolo_v5/`, `manifests/kimchi_v5/train.csv`·`val.csv`

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `RUNS` | 실행별 바꾸는 값 (10 의 `EXPERIMENTS` 에서 가져옴), 실행 이름, Weight 위치, 비교 대상 |
| `paths` | `SplitBuilder(PROJECT_ROOT, "kimchi_v5")` — v5 폴더 위치. 06 의 `DATA_YAML`·`MANIFEST_DIR`·`YOLO_DIR` 을 이 값으로 바꿔 `precheck()` 를 그대로 쓴다 |
| `train_one(key, counts)` | [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관 → 조건 기록 |
| `main()` | precheck (폴더 = manifest, Version = kimchi_v5) 후 `--run` 차례로 |

## 의존성

- **사용하는 것**: [`scripts/10_train_v2`](10_train_v2.md) (→ [`06`](06_train_baseline.md)), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행

## 주의사항

- 실행 폴더나 보관 Weight 가 이미 있으면 멈춘다 (덮어쓰지 않음). `all` 은 하나가 실패하면 거기서 멈춘다.
- v4 와는 Val 이 달라 점수를 직접 비교하지 않는다. 그래프는 [`plot_runs`](plot_runs.md) 가 실행 이름의 `_v5` 로 묶는다.
