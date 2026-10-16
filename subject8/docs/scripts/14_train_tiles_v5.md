# `subject8/scripts/14_train_tiles_v5.py`

> 개선 실험 **exp004_v5 — 타일링**: 4K 원본을 2×2 조각(20% 겹침)으로 잘라 학습하고, 조각 예측을 합쳐 원본 Val 104장으로 채점해 exp002_v5 와 비교한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/14_train_tiles_v5.py)

## 사용법

```bash
cd subject8
python scripts/14_train_tiles_v5.py              # 조각 만들기(없으면) → 학습 → 채점
python scripts/14_train_tiles_v5.py --eval-only  # 채점만
```

| 입력 | 출력 |
|---|---|
| `data/yolo/{images,labels}/{train,val}` (공식 v5) | `data/yolo_v5_tiles/` (조각, Git 제외), `configs/dataset_v5_tiles.yaml`, `runs/exp004_v5_tile2x2/`, `models/improved/exp004_v5_tile2x2.pt`, `reports/04_improvement/exp004_v5_tile2x2_training_condition.md`, `reports/04_improvement/tiling_eval.csv` |

결과 (2026-10-16, 원본 Val 104장 · 같은 채점 코드): exp002_v5 0.680 → **exp004_v5 0.698** (+0.019), Recall 0.781 → 0.814, 갈변 AP50-95 0.04 → 0.08, 나뭇잎·종이 0.78 → 0.74. 판정은 `experiment_log.csv` (보류 — 기준 +0.02 바로 아래).

| 바꾸는 변수 | 유지 | 비교 대상 |
|---|---|---|
| 입력: 원본 → 2×2 조각 (2693×1502, 원본 558·104장 → 조각 2232·416개) | YOLO11n · imgsz 1920 · batch 6 · 50 epoch · AdamW 0.001 · seed 42 · 기본 증강 | exp002_v5 (원본 1920) |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `TILES` | `((2, 2), 0.2)` — 조각 수·겹침 |
| `CONDITION` | 06 `BASELINE` + 11 의 exp002 바꾸는 값 (imgsz 1920 · batch 6) |
| `build_tiles()` | train·val 조각 만들기 (이미 있으면 건너뜀) + yaml |
| `train()` | [`train_detector`](../src/train_detector.md) → 점검 → Weight 보관 → 조건 기록 |
| `evaluate()` | [`tiling.evaluate_full`](../src/tiling.md) 로 원본 Val 채점 — exp002_v5 (원본 예측) · exp004_v5 (조각 예측 합침) |

## 의존성

- **사용하는 것**: [`src/tiling`](../src/tiling.md), [`scripts/11_train_v5`](11_train_v5.md) (조건), [`src/split_builder`](../src/split_builder.md), [`src/train_detector`](../src/train_detector.md)
- **사용하는 곳**: 직접 실행

## 주의사항

- Test · Bridge 는 조각을 만들지 않는다.
- 학습 중 Validation 은 조각 단위라 `runs_summary.csv` 의 다른 실행과 비교하지 않는다. 비교는 `tiling_eval.csv`.
- 사진이 4배라 학습이 exp002_v5 의 약 4배 (RTX 3060 약 90분).
