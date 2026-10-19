# 모델 목록

> `python scripts/plot_runs.py` 가 만드는 표입니다 (직접 고치지 않음). 점수는 **학습 중 best epoch 의 Validation** — 같은 Dataset Version 끼리만 비교합니다 (Version 마다 Validation 이 다름).

- 공식 Dataset Version: **`kimchi_v5`** (`src/constants.py` 의 `DEFAULT_DATASET_VERSION`)
- `baseline/baseline_best.pt` = **`baseline_v5`** 의 복사본
- 파일 이름 = `runs/` 폴더 이름. 공식 Version 은 `baseline/` · `improved/`, 지난 Version 은 `history/<Version>/`
- 사용: `python scripts/08_predict_images.py --model <실행>` · `09_collect_failures.py --model <실행>` (imgsz · 데이터는 자동)

## kimchi_v5 (공식)

| 실행 | 공식 | Weight | imgsz | epoch | batch | best ep | Val P | Val R | mAP50 | mAP50-95 | 조건 기록 | 그래프 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_v5` | baseline | [baseline/baseline_v5.pt](../models/baseline/baseline_v5.pt) | 640 | 50 | 16 | 44 | 0.888 | 0.589 | 0.688 | 0.469 | [기록](../reports/02_baseline/baseline_training_condition.md) | [학습 곡선](../reports/figures/runs/baseline_v5.png) · [Confusion](../runs/baseline_v5/confusion_matrix.png) · [PR](../runs/baseline_v5/BoxPR_curve.png) |
| `exp001_v5_imgsz1280` |  | [improved/exp001_v5_imgsz1280.pt](../models/improved/exp001_v5_imgsz1280.pt) | 1280 | 50 | 16 | 45 | 0.957 | 0.724 | 0.777 | 0.646 | [기록](../reports/04_improvement/exp001_v5_imgsz1280_training_condition.md) | [학습 곡선](../reports/figures/runs/exp001_v5_imgsz1280.png) · [Confusion](../runs/exp001_v5_imgsz1280/confusion_matrix.png) · [PR](../runs/exp001_v5_imgsz1280/BoxPR_curve.png) |
| `exp002_v5_imgsz1920` |  | [improved/exp002_v5_imgsz1920.pt](../models/improved/exp002_v5_imgsz1920.pt) | 1920 | 50 | 6 | 47 | 0.856 | 0.766 | 0.809 | 0.704 | [기록](../reports/04_improvement/exp002_v5_imgsz1920_training_condition.md) | [학습 곡선](../reports/figures/runs/exp002_v5_imgsz1920.png) · [Confusion](../runs/exp002_v5_imgsz1920/confusion_matrix.png) · [PR](../runs/exp002_v5_imgsz1920/BoxPR_curve.png) |
| `exp003_v5_imgsz1920_epoch100` |  | [improved/exp003_v5_imgsz1920_epoch100.pt](../models/improved/exp003_v5_imgsz1920_epoch100.pt) | 1920 | 100 | 6 | 87 | 0.872 | 0.788 | 0.801 | 0.701 | [기록](../reports/04_improvement/exp003_v5_imgsz1920_epoch100_training_condition.md) | [학습 곡선](../reports/figures/runs/exp003_v5_imgsz1920_epoch100.png) · [Confusion](../runs/exp003_v5_imgsz1920_epoch100/confusion_matrix.png) · [PR](../runs/exp003_v5_imgsz1920_epoch100/BoxPR_curve.png) |
| `exp004_v5_tile2x2` |  | [improved/exp004_v5_tile2x2.pt](../models/improved/exp004_v5_tile2x2.pt) | 1920 | 50 | 6 | 42 | 0.896 | 0.794 | 0.821 | 0.709 (조각 Val) | [기록](../reports/04_improvement/exp004_v5_tile2x2_training_condition.md) | [학습 곡선](../reports/figures/runs/exp004_v5_tile2x2.png) · [Confusion](../runs/exp004_v5_tile2x2/confusion_matrix.png) · [PR](../runs/exp004_v5_tile2x2/BoxPR_curve.png) |
| `exp005_v5_imgsz1920_aug` |  | [improved/exp005_v5_imgsz1920_aug.pt](../models/improved/exp005_v5_imgsz1920_aug.pt) | 1920 | 50 | 6 | 50 | 0.841 | 0.760 | 0.800 | 0.684 | [기록](../reports/04_improvement/exp005_v5_imgsz1920_aug_training_condition.md) | [학습 곡선](../reports/figures/runs/exp005_v5_imgsz1920_aug.png) · [Confusion](../runs/exp005_v5_imgsz1920_aug/confusion_matrix.png) · [PR](../runs/exp005_v5_imgsz1920_aug/BoxPR_curve.png) |
| `exp006_v5_imgsz2560_aug` |  | [improved/exp006_v5_imgsz2560_aug.pt](../models/improved/exp006_v5_imgsz2560_aug.pt) | 2560 | 50 | 3 | 49 | 0.872 | 0.814 | 0.832 | 0.722 | [기록](../reports/04_improvement/exp006_v5_imgsz2560_aug_training_condition.md) | [학습 곡선](../reports/figures/runs/exp006_v5_imgsz2560_aug.png) · [Confusion](../runs/exp006_v5_imgsz2560_aug/confusion_matrix.png) · [PR](../runs/exp006_v5_imgsz2560_aug/BoxPR_curve.png) |
| `exp007_v5_s_imgsz1920_aug` |  | [improved/exp007_v5_s_imgsz1920_aug.pt](../models/improved/exp007_v5_s_imgsz1920_aug.pt) | 1920 | 50 | 3 | 50 | 0.956 | 0.794 | 0.824 | 0.724 | [기록](../reports/04_improvement/exp007_v5_s_imgsz1920_aug_training_condition.md) | [학습 곡선](../reports/figures/runs/exp007_v5_s_imgsz1920_aug.png) · [Confusion](../runs/exp007_v5_s_imgsz1920_aug/confusion_matrix.png) · [PR](../runs/exp007_v5_s_imgsz1920_aug/BoxPR_curve.png) |
| `exp008_v5_s_imgsz1920_aug_epoch100` |  | [improved/exp008_v5_s_imgsz1920_aug_epoch100.pt](../models/improved/exp008_v5_s_imgsz1920_aug_epoch100.pt) | 1920 | 100 | 3 | 87 | 0.952 | 0.795 | 0.828 | 0.727 | [기록](../reports/04_improvement/exp008_v5_s_imgsz1920_aug_epoch100_training_condition.md) | [학습 곡선](../reports/figures/runs/exp008_v5_s_imgsz1920_aug_epoch100.png) · [Confusion](../runs/exp008_v5_s_imgsz1920_aug_epoch100/confusion_matrix.png) · [PR](../runs/exp008_v5_s_imgsz1920_aug_epoch100/BoxPR_curve.png) |
| `exp010_v5_s_tile2x2_aug` |  | [improved/exp010_v5_s_tile2x2_aug.pt](../models/improved/exp010_v5_s_tile2x2_aug.pt) | 1920 | 50 | 3 | 49 | 0.897 | 0.763 | 0.814 | 0.712 (조각 Val) | [기록](../reports/04_improvement/exp010_v5_s_tile2x2_aug_training_condition.md) | [학습 곡선](../reports/figures/runs/exp010_v5_s_tile2x2_aug.png) · [Confusion](../runs/exp010_v5_s_tile2x2_aug/confusion_matrix.png) · [PR](../runs/exp010_v5_s_tile2x2_aug/BoxPR_curve.png) |
| `exp010b_v5_s_tile2x2_aug` |  | [improved/exp010b_v5_s_tile2x2_aug.pt](../models/improved/exp010b_v5_s_tile2x2_aug.pt) | 1920 | 50 | 3 | 49 | 0.897 | 0.763 | 0.814 | 0.712 (조각 Val) | [기록](../reports/04_improvement/exp010b_v5_s_tile2x2_aug_training_condition.md) | [학습 곡선](../reports/figures/runs/exp010b_v5_s_tile2x2_aug.png) · [Confusion](../runs/exp010b_v5_s_tile2x2_aug/confusion_matrix.png) · [PR](../runs/exp010b_v5_s_tile2x2_aug/BoxPR_curve.png) |
| `exp012_v5_s_imgsz1280_aug` |  | [improved/exp012_v5_s_imgsz1280_aug.pt](../models/improved/exp012_v5_s_imgsz1280_aug.pt) | 1280 | 50 | 6 | 35 | 0.748 | 0.741 | 0.785 | 0.680 | [기록](../reports/04_improvement/exp012_v5_s_imgsz1280_aug_training_condition.md) | [학습 곡선](../reports/figures/runs/exp012_v5_s_imgsz1280_aug.png) · [Confusion](../runs/exp012_v5_s_imgsz1280_aug/confusion_matrix.png) · [PR](../runs/exp012_v5_s_imgsz1280_aug/BoxPR_curve.png) |
| `exp013_v5_s_imgsz1920_aug_seed7` |  | [improved/exp013_v5_s_imgsz1920_aug_seed7.pt](../models/improved/exp013_v5_s_imgsz1920_aug_seed7.pt) | 1920 | 50 | 3 | 47 | 0.827 | 0.808 | 0.817 | 0.714 | [기록](../reports/04_improvement/exp013_v5_s_imgsz1920_aug_seed7_training_condition.md) | [학습 곡선](../reports/figures/runs/exp013_v5_s_imgsz1920_aug_seed7.png) · [Confusion](../runs/exp013_v5_s_imgsz1920_aug_seed7/confusion_matrix.png) · [PR](../runs/exp013_v5_s_imgsz1920_aug_seed7/BoxPR_curve.png) |

## kimchi_v4

| 실행 | 공식 | Weight | imgsz | epoch | batch | best ep | Val P | Val R | mAP50 | mAP50-95 | 조건 기록 | 그래프 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_v4` |  | [history/kimchi_v4/baseline_v4.pt](../models/history/kimchi_v4/baseline_v4.pt) | 640 | 50 | 16 | 50 | 0.837 | 0.674 | 0.764 | 0.534 | [기록](../reports/history/kimchi_v4/baseline_v4_training_condition.md) | [학습 곡선](../reports/figures/runs/baseline_v4.png) · [Confusion](../runs/baseline_v4/confusion_matrix.png) · [PR](../runs/baseline_v4/BoxPR_curve.png) |
| `exp001_v4_imgsz1280` |  | [history/kimchi_v4/exp001_v4_imgsz1280.pt](../models/history/kimchi_v4/exp001_v4_imgsz1280.pt) | 1280 | 50 | 16 | 39 | 0.939 | 0.782 | 0.884 | 0.708 | [기록](../reports/history/kimchi_v4/exp001_v4_imgsz1280_training_condition.md) | [학습 곡선](../reports/figures/runs/exp001_v4_imgsz1280.png) · [Confusion](../runs/exp001_v4_imgsz1280/confusion_matrix.png) · [PR](../runs/exp001_v4_imgsz1280/BoxPR_curve.png) |
| `exp002_v4_imgsz1920` |  | [history/kimchi_v4/exp002_v4_imgsz1920.pt](../models/history/kimchi_v4/exp002_v4_imgsz1920.pt) | 1920 | 50 | 6 | 50 | 0.944 | 0.816 | 0.891 | 0.757 | [기록](../reports/history/kimchi_v4/exp002_v4_imgsz1920_training_condition.md) | [학습 곡선](../reports/figures/runs/exp002_v4_imgsz1920.png) · [Confusion](../runs/exp002_v4_imgsz1920/confusion_matrix.png) · [PR](../runs/exp002_v4_imgsz1920/BoxPR_curve.png) |
| `exp003_v4_imgsz1920_epoch100` |  | [history/kimchi_v4/exp003_v4_imgsz1920_epoch100.pt](../models/history/kimchi_v4/exp003_v4_imgsz1920_epoch100.pt) | 1920 | 100 | 6 | 77 | 0.929 | 0.816 | 0.913 | 0.774 | [기록](../reports/history/kimchi_v4/exp003_v4_imgsz1920_epoch100_training_condition.md) | [학습 곡선](../reports/figures/runs/exp003_v4_imgsz1920_epoch100.png) · [Confusion](../runs/exp003_v4_imgsz1920_epoch100/confusion_matrix.png) · [PR](../runs/exp003_v4_imgsz1920_epoch100/BoxPR_curve.png) |

## kimchi_v3

| 실행 | 공식 | Weight | imgsz | epoch | batch | best ep | Val P | Val R | mAP50 | mAP50-95 | 조건 기록 | 그래프 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `history_v3_imgsz1280` |  | [history/kimchi_v3/history_v3_imgsz1280.pt](../models/history/kimchi_v3/history_v3_imgsz1280.pt) | 1280 | 50 | 16 | 40 | 0.683 | 0.667 | 0.701 | 0.575 | [기록](../reports/history/kimchi_v3/history_v3_imgsz1280_training_condition.md) | [학습 곡선](../reports/figures/runs/history_v3_imgsz1280.png) · [Confusion](../runs/history_v3_imgsz1280/confusion_matrix.png) · [PR](../runs/history_v3_imgsz1280/BoxPR_curve.png) |

## kimchi_v2

| 실행 | 공식 | Weight | imgsz | epoch | batch | best ep | Val P | Val R | mAP50 | mAP50-95 | 조건 기록 | 그래프 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `history_v2_imgsz1280` |  | [history/kimchi_v2/history_v2_imgsz1280.pt](../models/history/kimchi_v2/history_v2_imgsz1280.pt) | 1280 | 50 | 16 | 47 | 0.698 | 0.672 | 0.708 | 0.575 | [기록](../reports/history/kimchi_v2/history_v2_imgsz1280_training_condition.md) | [학습 곡선](../reports/figures/runs/history_v2_imgsz1280.png) · [Confusion](../runs/history_v2_imgsz1280/confusion_matrix.png) · [PR](../runs/history_v2_imgsz1280/BoxPR_curve.png) |

## kimchi_v1

| 실행 | 공식 | Weight | imgsz | epoch | batch | best ep | Val P | Val R | mAP50 | mAP50-95 | 조건 기록 | 그래프 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_v1` |  | [history/kimchi_v1/baseline_v1.pt](../models/history/kimchi_v1/baseline_v1.pt) | 640 | 50 | 16 | 45 | 0.428 | 0.479 | 0.491 | 0.347 | [기록](../reports/history/kimchi_v1/baseline_v1_training_condition.md) | [학습 곡선](../reports/figures/runs/baseline_v1.png) · [Confusion](../runs/baseline_v1/confusion_matrix.png) · [PR](../runs/baseline_v1/BoxPR_curve.png) |
| `pilot_v1_imgsz1280` |  | 보관 안 함 | 1280 | 50 | 16 | 40 | 0.690 | 0.549 | 0.635 | 0.519 |  | [학습 곡선](../reports/figures/runs/pilot_v1_imgsz1280.png) · [Confusion](../runs/pilot_v1_imgsz1280/confusion_matrix.png) · [PR](../runs/pilot_v1_imgsz1280/BoxPR_curve.png) |
