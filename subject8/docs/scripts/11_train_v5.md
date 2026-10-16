# `subject8/scripts/11_train_v5.py`

> 공식 Version `kimchi_v5`(C안 재분할) 학습 — [`06`](06_train_baseline.md) Baseline 조건과 한 변수 개선 실험(해상도 · epoch · 증강)을 v5 데이터에서 한다. 타일링(exp004)은 [`14`](14_train_tiles_v5.md).

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/11_train_v5.py)

## 사용법

```bash
cd subject8
python scripts/00_setup.py                                   # 먼저 data/yolo (v5) 준비
python scripts/11_train_v5.py --run exp001                   # 하나만 (all = 차례로 전부, 이미 Weight 가 있으면 멈춤)
python scripts/11_train_v5.py --run exp005 --report-only     # 학습은 끝났는데 조건 기록만 다시 쓸 때
```

| `--run` | 조건 (06 에서 바꾸는 값) | 실행 폴더 = Weight 이름 | 결과 (v5 Val mAP50-95) |
|---|---|---|---|
| `baseline` | 그대로 (imgsz 640) | `baseline_v5` | 0.470 |
| `exp001` | imgsz 1280 | `exp001_v5_imgsz1280` | 0.646 |
| `exp002` | imgsz 1920 · batch 6 | `exp002_v5_imgsz1920` | 0.704 |
| `exp003` | exp002 + epochs 100 | `exp003_v5_imgsz1920_epoch100` | 0.701 |
| `exp005` | exp002 + 증강 (상하반전 flipud 0.5 · 밝기 hsv_v 0.6) | `exp005_v5_imgsz1920_aug` | 0.684 |

- Weight: `models/baseline/` · `models/improved/<실행>.pt` ([`registry.weight_path`](../src/registry.md))
- 조건 기록: `baseline` → `reports/02_baseline/baseline_training_condition.md` (가이드 이름), 그 밖 → `reports/04_improvement/<실행>_training_condition.md`
- 입력: `configs/dataset.yaml`, `data/yolo/`, `manifests/train.csv`·`val.csv`

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `RUNS` | 실행별 바꾸는 값 (10 의 `EXPERIMENTS` 에서 가져옴 · exp005 는 여기서 정의), 실행 이름, 비교 대상, 메모 |
| `ULTRALYTICS_DEFAULTS` | 06 `BASELINE` 에 없는 증강 값의 기본값 — 조건 기록에 "기본 → 바꾼 값" 으로 적는다 |
| `paths` | `SplitBuilder(PROJECT_ROOT, "kimchi_v5")` — 06 의 `DATA_YAML`·`MANIFEST_DIR`·`YOLO_DIR` 을 이 값으로 바꿔 `precheck()` 를 그대로 쓴다 |
| `finished_result(run)` | 이미 끝난 실행의 결과 dict (`--report-only`) — 시작·종료 시각은 `args.yaml`·`results.csv` 파일 시각 |
| `train_one(key, counts, report_only)` | [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관 → 조건 기록 |
| `main()` | precheck (폴더 = manifest, Version = kimchi_v5) 후 `--run` 차례로 |

## 의존성

- **사용하는 것**: [`scripts/10_train_v2`](10_train_v2.md) (→ [`06`](06_train_baseline.md)), [`src/registry`](../src/registry.md), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행, [`14_train_tiles_v5`](14_train_tiles_v5.md) 가 조건(`RUNS`)을 가져다 쓴다

## 주의사항

- 실행 폴더나 보관 Weight 가 이미 있으면 멈춘다 (덮어쓰지 않음). `all` 은 하나가 실패하면 거기서 멈춘다.
- v4 와는 Val 이 달라 점수를 직접 비교하지 않는다. 실험 판정은 `reports/04_improvement/experiment_log.csv`.
- exp005 는 학습 후 조건 기록 단계에서 오류(BASELINE 에 없는 `flipud`)가 나 `--report-only` 로 기록만 다시 썼다 (학습·Weight 는 정상).
