# reports 안내

파일 이름은 가이드와 같은 영어 이름 그대로이고, **단계(일차)별 폴더만 추가**했다. 단계 폴더(01~05)는 **공식 Dataset Version `kimchi_v5`** 의 결과이고, 지난 Version 은 `history/<Version>/` 에 같은 이름 규칙으로 둔다.

```text
reports/
├── 01_data/                  2~3일차  Dataset 수량 · 점검 · 라벨 수정 기록 · v4→v5 비교
│   ├── label_fixes_kimchi_v3/    Class 5(갈변) 재검수와 라벨 수정 내역
│   └── label_fixes_kimchi_v5/    v5 에서 지운 박스 3개 (이물 없음)
├── 02_baseline/              4~5일차  공식 Baseline(baseline_v5) 학습 조건 · Validation 성능
├── 03_failure_analysis/      6일차    실패 사례 표 (baseline_v5) — 원인 가설 문서는 v5 기준으로 다시 작성 예정
├── 04_improvement/           7일차    v5 실험 기록 · 실험별 학습 조건 · 타일링 채점
├── 05_final/                 8일차    Frozen Test (Final exp050, 한 번) — final_metrics.csv · final_class_metrics.csv
├── final_model_selection.md  8일차    Final Model 선택 근거 (후보별 seed 평균 · 4라운드 · 갈변)
├── 05_acceptance/            9일차    Acceptance Test (담당 5번 — Final · Frozen Test 반영, Auto Label 은 TODO)
├── runs_summary.csv          모든 Version 의 모든 학습 실행 요약 (scripts/plot_runs.py 가 생성)
├── history/                  지난 Dataset Version — 현재 기준 아님, 지우지 않고 남긴 기록
│   ├── kimchi_v1/ · kimchi_v2/ · kimchi_v3/ · kimchi_v4/
│   └── smoke_test.md
└── figures/
    ├── baseline/             공식 Baseline 학습 곡선 · Confusion Matrix · PR 곡선 (07 이 생성)
    ├── runs/                 실행마다의 학습 곡선 (모든 Version)
    └── comparison/           Version 별 실행 비교 · v4→v5 비교
```

> **먼저 볼 파일**
> 0. [`final_model_selection.md`](final_model_selection.md) · [`05_final/final_metrics.csv`](05_final/final_metrics.csv) — Final Model 과 Frozen Test 결과 · 교과 14 인계 [`../docs/handoff_subject14.md`](../docs/handoff_subject14.md)
> 1. [`../models/README.md`](../models/README.md) — 모든 모델의 Version · 점수 · 조건 기록 · 그래프 링크 (자동 생성)
> 2. [`04_improvement/baseline_vs_improved.md`](04_improvement/baseline_vs_improved.md) — v5 개선점 · 한계점 (발표용), [`experiment_log.csv`](04_improvement/experiment_log.csv) — 실험별 판정
> 3. [`figures/comparison/runs_comparison_kimchi_v5.png`](figures/comparison/runs_comparison_kimchi_v5.png) — v5 실험 비교 그림
> 4. [`figures/comparison/v5_vs_v4.png`](figures/comparison/v5_vs_v4.png) — v4 → v5 에서 달라진 점 (누수 · Class 박스 · 점수)

## 폴더별 파일

### 01_data (2~3일차)

| 파일 | 내용 |
|---|---|
| `dataset_summary.csv` | `kimchi_v5` 의 Train / Val / Test / Bridge Holdout 장수 — 558 / 104 / 82 / 156 (산출물 1) |
| `v5_vs_v4.csv` | v4 → v5 비교 숫자 (평가 사진의 같은 묶음 출신 수, 역할 × Class 박스, Val 점수) — `scripts/plot_v5_vs_v4.py` |
| `audit_summary.csv`, `audit_class_scene.csv` | 전체 수량 · Class × 장면 (2일차 Data Audit, Version 무관) |
| `audit_issue.csv` | 발견된 오류 (비어 있음 = 오류 없음) |
| `capture_group_summary.csv`, `leakage_check.csv` | 촬영 묶음별 장수·시간·장면 · 사진 지문 누수 점검 |
| `label_fixes_kimchi_v3/` | 갈변 재검수 표 · 사람 확인 작업표 · v3 라벨 수정 내역 |
| `label_fixes_kimchi_v5/label_changes_kimchi_v5.csv` | v5 에서 지운 박스 3개 |

### 02_baseline (4~5일차)

| 파일 | 내용 |
|---|---|
| `baseline_training_condition.md` | 공식 Baseline `baseline_v5` 학습 조건 (산출물 2) |
| `baseline_metrics.csv`, `baseline_class_metrics.csv` | Validation 104장 성능 · Class 별 성능 (`scripts/07_evaluate_baseline.py`) |

### 03_failure_analysis (6일차)

| 파일 | 내용 |
|---|---|
| `failure_analysis.csv` | 정답·오검출 하나하나의 결과 (산출물 3, `scripts/09_collect_failures.py`) |
| `failure_summary.csv` | 실패 유형 × Class 별 건수 |
| `failure_recall_by_size.csv` | 박스 크기별 Recall |
| `failure_box_size_shift.csv` | Train vs Val 박스 크기 차이 |
| `exp050_v5_s_imgsz2240_aug_seed2_failure_*.csv` (4개) | **Final 모델**의 Validation 실패 사례 표 (같은 방법 · `09_collect_failures.py --model final`) — Baseline 과 비교는 `failure_hypothesis.md` 6장 |
| `failure_hypothesis.md` | v5 기준 원인 가설 H1~H5 와 이후 검증, Final 의 남은 실패 (산출물 3) — kimchi_v1 때의 가설은 `history/kimchi_v1/03_failure_analysis/` |

### 04_improvement (7일차)

| 파일 | 내용 |
|---|---|
| **`experiment_log.csv`** | v5 실험 기록 · 판정 (산출물 5) |
| `<실행>_training_condition.md` | exp001~050 의 학습 조건 (해상도 · epoch · 타일링 · 증강 · 모델 11n/11s/11m · 4라운드 갈변 개선 6방향 × seed 5개) |
| `tiling_eval.csv` | 타일링 비교 — 원본 Val 104장을 같은 코드로 채점 (exp002_v5 원본 vs exp004_v5 조각 합침) |
| **`baseline_vs_improved.md`** | v5 실험 비교 · **개선점 · 한계점** (발표용) · Final 후보 (산출물 5) |
| `improvement_experiment.md` | v5 개선 실험 설계 · 기록 · Final 결정 (산출물 4) — v4 판은 `history/kimchi_v4/` |
| `tiling_eval_exp010.csv` | (예정) exp010 11s 타일링 채점 |

### 05_final (8일차)

| 파일 | 내용 |
|---|---|
| `final_metrics.csv` | Frozen Test 82장 성능 — Final `exp050` · mAP50-95 0.639 (산출물 5, `scripts/16_evaluate_final_test.py`) |
| `final_class_metrics.csv` | Class 별 Test 성능 (갈변 Recall 0.00 · Class 4 는 Instance 0건) |
| `../final_model_selection.md` | Final 선택 근거 (Validation 기준 — Test 로 고르지 않음) |

### 05_acceptance (9일차)

| 파일 | 내용 |
|---|---|
| `acceptance_test.md` | Acceptance Test 결과 (작성 중 — 7일차 자동 점검 기준, 담당 5번) |
| `acceptance_check.csv` | 자동 점검 원본 (`scripts/qa_acceptance_check.py`) |

### history (지난 Version)

| 폴더 | 내용 |
|---|---|
| `kimchi_v1/` | 첫 Baseline `baseline_v1` 조건·성능·그래프, 그 실패 분석 `03_failure_analysis/` (H1~H5 — v2~v4 로 Dataset 을 고친 근거) |
| `kimchi_v2/` · `kimchi_v3/` | 데이터 개선 과정 1280 학습 조건 |
| `kimchi_v4/` | `baseline_v4` · exp001~003 조건·성능, v4 개선 분석 `baseline_vs_improved.md` · `improvement_experiment.md` · `experiment_log.csv`, 그래프 `figures/` |
| `smoke_test.md` | Smoke Test 점검 |

Dataset Version 마다 Val 구성이 달라 **v5 점수와 직접 비교하지 않는다.**

## 학습 실행 한눈에 (kimchi_v5, `runs_summary.csv` · `04_improvement/experiment_log.csv`)

| 실행 | imgsz | epochs | 바꾼 것 | Val mAP50-95 | 판정 |
|---|---:|---:|---|---:|---|
| `baseline_v5` (공식 Baseline) | 640 | 50 | — | 0.470 | 기준 |
| `exp001_v5_imgsz1280` | 1280 | 50 | imgsz | 0.646 | 채택 |
| `exp002_v5_imgsz1920` | 1920 | 50 | imgsz (batch 6) | **0.704** | 채택 |
| `exp003_v5_imgsz1920_epoch100` | 1920 | 100 | epochs | 0.701 | 기각 |
| `exp004_v5_tile2x2` | 1920 | 50 | 2×2 타일링 | 0.698* (원본 단위, exp002 = 0.680*) | 보류 |
| `exp005_v5_imgsz1920_aug` | 1920 | 50 | 증강 | 0.684 | 기각 |
| `exp006_v5_imgsz2560_aug` | 2560 | 50 | 증강 + 해상도 (두 변수) | 0.722 | 보류 (학습 5시간) |
| `exp007_v5_s_imgsz1920_aug` | 1920 | 50 | 증강 + YOLO11s (두 변수) | **0.724** | 채택 후보 (후보 A, 평균 0.715) |
| `exp015·016·018·049·050` (후보 B) | 2240 | 50 | exp007 + imgsz 2240 (batch 2) | 평균 **0.739** (0.726~0.749) | 선택 |
| **`exp050_v5_s_imgsz2240_aug_seed2`** | 2240 | 50 | B 의 seed 2 | **0.749** · Frozen Test **0.639** | **Final Model** |
| exp019~048 (4라운드 6방향 × seed 5개) | 2240 · 2560 | 50 | 반점 복제 · 합성 · 복원 · 2560 · 조합 | 평균 0.726~0.740 | 모두 B 보다 +0.02 미달 (갈변 개선 실패) |

(exp009 · 011 · 014 등 나머지는 [`04_improvement/experiment_log.csv`](04_improvement/experiment_log.csv) 52행 참고)

\* `src/tiling.py` 로 원본 사진 단위 채점. 학습 곡선은 `figures/runs/<실행>.png`, Confusion Matrix · PR 곡선은 `../runs/<실행>/`, Weight 는 [`../models/README.md`](../models/README.md).
