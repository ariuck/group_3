# `subject8/scripts/14_train_tiles_v5.py`

> 타일링 실험: 4K 원본을 2×2 조각(20% 겹침)으로 잘라 학습하고, 조각 예측을 합쳐 원본 Val 104장으로 채점해 같은 조건의 원본 입력 모델과 비교한다. **exp004** (exp002 = 11n · 1920 기준), **exp010** (exp007 = 11s · 1920 · 증강 기준).

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/14_train_tiles_v5.py)

## 사용법

```bash
cd subject8
python scripts/14_train_tiles_v5.py                            # exp004: 조각 만들기(없으면) → 학습 → 채점
python scripts/14_train_tiles_v5.py --exp exp010               # exp010: 11s · 증강 + 조각
python scripts/14_train_tiles_v5.py --exp exp010 --eval-only   # 채점만
```

| `--exp` | 실행 이름 | 기준 실험 (같은 조건 · 원본 입력) | 채점 CSV |
|---|---|---|---|
| `exp004` | `exp004_v5_tile2x2` | `exp002_v5_imgsz1920` (11n · batch 6) | `reports/04_improvement/tiling_eval.csv` |
| `exp010` | `exp010_v5_s_tile2x2_aug` | `exp007_v5_s_imgsz1920_aug` (11s · batch 3 · 증강) | `reports/04_improvement/tiling_eval_exp010.csv` |

| 입력 | 출력 |
|---|---|
| `data/yolo/{images,labels}/{train,val}` (공식 v5) | `data/yolo_v5_tiles/` (조각, Git 제외, 두 실험이 같이 씀), `configs/dataset_v5_tiles.yaml`, `runs/<실행>/`, `models/improved/<실행>.pt`, `reports/04_improvement/<실행>_training_condition.md`, 채점 CSV |

결과 exp004 (2026-10-16, 원본 Val 104장 · 같은 채점 코드): exp002_v5 0.680 → **exp004_v5 0.698** (+0.019), Recall 0.781 → 0.814, 갈변 AP50-95 0.04 → 0.08, 나뭇잎·종이 0.78 → 0.74 (보류). exp010 은 3대 분산 실험에서 진행 ([experiment_handoff](../project/experiment_handoff.md)).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `TILES` | `((2, 2), 0.2)` — 조각 수·겹침 |
| `TILE_EXPS` | `--exp` → (실행 이름, 기준 실험 키, 채점 CSV) |
| `select(exp)` | `RUN_NAME`·`WEIGHT`·`REPORT`·`EVAL_CSV`·`COMPARE_RUN`·`CONDITION`(= 06 `BASELINE` + 11 의 기준 실험 바꾸는 값) 을 정한다 |
| `build_tiles()` | train·val 조각 만들기 (이미 있으면 건너뜀) + yaml |
| `train()` | [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관 → 조건 기록 |
| `evaluate()` | [`tiling.evaluate_full`](../src/tiling.md) 로 원본 Val 채점 — 기준 실험 (원본 예측) · 타일링 (조각 예측 합침) |

## 의존성

- **사용하는 것**: [`src/tiling`](../src/tiling.md), [`scripts/11_train_v5`](11_train_v5.md) (조건 `RUNS`), [`src/registry`](../src/registry.md), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행

## 주의사항

- Test · Bridge 는 조각을 만들지 않는다.
- 학습 중 Validation 은 조각 단위라 `runs_summary.csv` 의 다른 실행과 비교하지 않는다. 비교는 채점 CSV.
- 사진이 4배라 학습이 기준 실험의 약 4배 (RTX 3060: exp004 약 90분, exp010 약 3시간 예상).
