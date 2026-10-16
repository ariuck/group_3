# reports 안내

파일 이름은 가이드와 같은 영어 이름 그대로이고, **단계(일차)별 폴더만 추가**했다.

```text
reports/
├── 01_data/                  2~3일차  Dataset 수량 · 점검 · 라벨 수정 기록
│   ├── label_fixes_kimchi_v3/    Class 5(갈변) 재검수와 라벨 수정 내역
│   └── label_fixes_kimchi_v5/    v5 에서 지운 박스 3개 (이물 없음)
├── 02_baseline/              4~5일차  Baseline 학습 조건 · Validation 성능
├── 03_failure_analysis/      6일차    실패 사례 표 · 원인 가설
├── 04_improvement/           7일차    설계 · 실험 기록 · 비교 분석 · exp001~003 조건
├── 05_acceptance/            9일차    Acceptance Test 결과
├── 06_kimchi_v5/             재분할   kimchi_v5(C안) 학습 조건 — baseline_v5 · exp001_v5 · exp002_v5
├── history/                  지난 Dataset Version(v1~v3) · Smoke Test — 현재 기준 아님
└── figures/
    ├── baseline/             Baseline 학습 곡선 · Confusion Matrix · PR 곡선
    ├── runs/                 실행마다의 학습 곡선 (baseline_v4, exp001~003 …)
    ├── comparison/           Version 별 실행 비교 · 개선 분석 요약 그림
    └── history/              첫 Baseline(kimchi_v1) 그래프
```

> **먼저 볼 파일 4개**
> 1. [`04_improvement/baseline_vs_improved.md`](04_improvement/baseline_vs_improved.md) — 개선 결과 분석 (그림 포함)
> 2. [`04_improvement/runs_summary.csv`](04_improvement/runs_summary.csv) — 모든 학습 실행의 조건·성능을 한 표로 (자동 생성)
> 3. [`04_improvement/experiment_log.csv`](04_improvement/experiment_log.csv) — 실험별 변경 변수·이유·판정
> 4. [`04_improvement/improvement_experiment.md`](04_improvement/improvement_experiment.md) — exp001 이 무엇을 왜 바꿨는지

## 폴더별 파일

### 01_data (2~3일차)

| 파일 | 내용 |
|---|---|
| `dataset_summary.csv` | `kimchi_v4` 의 Train / Val / Test / Bridge Holdout 장수 (3일차) |
| `dataset_summary_kimchi_v5.csv` | `kimchi_v5`(C안) 장수 — 558 / 104 / 82 / 156 |
| `audit_summary.csv`, `audit_class_scene.csv` | 전체 수량 · Class × 장면 (2일차 Data Audit) |
| `audit_issue.csv` | 발견된 오류 (비어 있음 = 오류 없음) |
| `capture_group_summary.csv`, `leakage_check.csv` | 촬영 묶음별 장수·시간·장면 · Split 간 누수 점검 |
| `label_fixes_kimchi_v3/class5_review.csv`, `class5_relabel_worklist.csv` | 갈변 재검수 표 · 사람 확인 작업표 |
| `label_fixes_kimchi_v3/label_changes_kimchi_v3.csv` | v3 에서 Class 5 라벨을 고친 내역 (파일별) |

### 02_baseline (4~5일차)

| 파일 | 내용 |
|---|---|
| `baseline_training_condition.md` | 공식 Baseline `baseline_v4` 학습 조건 |
| `baseline_metrics.csv`, `baseline_class_metrics.csv` | Validation 성능 · Class별 성능 |

### 03_failure_analysis (6일차)

| 파일 | 내용 |
|---|---|
| **`failure_hypothesis.md`** | 실패 원인 가설 H1~H5 (읽을 문서) |
| `failure_analysis.csv` | 정답·오검출 하나하나의 결과 (가장 큰 파일) |
| `failure_summary.csv` | 실패 유형 × Class 별 건수 |
| `failure_recall_by_size.csv` | 박스 크기별 Recall (H4 근거) |
| `failure_box_size_shift.csv` | Train vs Val 박스 크기 차이 (H1 근거) |

### 04_improvement (7일차)

| 파일 | 내용 |
|---|---|
| **`improvement_experiment.md`** | exp001 설계: 변경 변수 · 유지 조건 · 확인 지표 |
| **`experiment_log.csv`** | 전체 실험 기록 (실패·이력 포함) |
| **`baseline_vs_improved.md`** | Baseline 과 exp001~003 비교 · Class별 · 비용 · Final Model 후보 제안 |
| `improvement_summary.csv` | 위 분석의 숫자 (`scripts/plot_improvement.py` 가 생성) |
| `exp001_training_condition.md` | imgsz 640 → 1280 |
| `exp002_training_condition.md` | imgsz 1280 → 1920 (batch 16 → 6 동반) |
| `exp003_training_condition.md` | epochs 50 → 100 |
| `runs_summary.csv` | 전 실행 요약 (`scripts/plot_runs.py` 가 생성) |

### 05_acceptance (9일차)

| 파일 | 내용 |
|---|---|
| `acceptance_test.md` | Acceptance Test 결과 (작성 중 — 7일차 자동 점검 기준) |
| `acceptance_check.csv` | 자동 점검 원본 (`scripts/qa_acceptance_check.py`) |

### history

`baseline_v1_*` (kimchi_v1 첫 Baseline — 6일차 실패분석의 대상), `history_v2_*`·`history_v3_*` (kimchi_v2·v3 학습 조건), `smoke_test.md`.
Dataset Version 마다 Val 구성이 달라 **`v4` 점수와 비교하지 않는다.** 지우지 않고 남긴 기록이다.

## 학습 실행 한눈에 (`04_improvement/runs_summary.csv` 요약)

| 실행 | Dataset | imgsz | epochs | mAP50-95 | 학습 곡선 |
|---|---|---:|---:|---:|---|
| `baseline_v4` (공식 Baseline) | v4 | 640 | 50 | 0.534 | `figures/runs/baseline_v4.png` |
| `exp001_v4_imgsz1280` | v4 | 1280 | 50 | 0.708 | `figures/runs/exp001_v4_imgsz1280.png` |
| `exp002_v4_imgsz1920` | v4 | 1920 | 50 | 0.758 | `figures/runs/exp002_v4_imgsz1920.png` |
| `exp003_v4_imgsz1920_epoch100` (Val 최고) | v4 | 1920 | 100 | 0.774 | `figures/runs/exp003_v4_imgsz1920_epoch100.png` |

Weight 는 `models/baseline/`, `models/improved/` 에 있다.

## 7일차 Daily Gate 에서 아직 없는 것

- exp001 Confusion Matrix (`figures/baseline/` 에는 Baseline 것만 있다 — 사진이 있는 PC 에서 필요). 학습 곡선은 `figures/runs/exp001_v4_imgsz1280.png` 로 이미 있으나 가이드가 정한 이름(`exp001_results.png`)과 다르다.
- 개선 모델의 크기별 Recall·CLASS_ERROR 재집계 (사진이 있는 PC 에서 `09_collect_failures.py`, 명령은 `04_improvement/baseline_vs_improved.md` 5장)
