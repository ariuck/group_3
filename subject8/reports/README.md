# reports 안내

```text
reports/
├── (바로 아래) 가이드가 요구하는 산출물 · 실험 기록
├── audit/      2일차 Data Audit 결과
├── class5/     Class 5(갈변) 재검수 · kimchi_v3 라벨 수정 기록
├── failure/    6일차 실패분석의 상세 표
├── history/    지난 Dataset Version(v1~v3)·Smoke Test 이력 — 현재 기준 아님
└── figures/    그래프
    ├── baseline/     공식 Baseline 학습 곡선 · Confusion Matrix · PR 곡선
    ├── runs/         실행별 학습 곡선 (baseline_v4, exp001~003 …)
    ├── comparison/   Dataset Version 별 실행 비교 (Val mAP50-95)
    └── history/      첫 Baseline(kimchi_v1) 그래프
```

> **먼저 볼 파일 3개**
> 1. [`runs_summary.csv`](runs_summary.csv) — 모든 학습 실행의 조건·성능을 한 표로 (자동 생성)
> 2. [`experiment_log.csv`](experiment_log.csv) — 실험별 변경 변수·이유·판정
> 3. [`improvement_experiment.md`](improvement_experiment.md) — exp001 이 무엇을 왜 바꿨는지

## reports/ 바로 아래 (산출물)

| 파일 | 일차 | 내용 |
|---|---|---|
| `dataset_summary.csv` | 3일차 | `kimchi_v4` 의 Train / Val / Test / Bridge Holdout 장수 |
| `baseline_training_condition.md` | 4일차 | 공식 Baseline `baseline_v4` 학습 조건 |
| `baseline_metrics.csv`, `baseline_class_metrics.csv` | 5일차 | `baseline_v4` 의 Validation 성능 · Class별 성능 |
| **`failure_hypothesis.md`** | 6일차 | 실패 원인 가설 H1~H5 (읽을 문서) |
| `failure_analysis.csv` | 6일차 | 정답·오검출 하나하나의 결과 (가장 큰 파일) |
| **`improvement_experiment.md`** | 7일차 | exp001 설계: 변경 변수·유지 조건·확인 지표 |
| **`experiment_log.csv`** | 7일차 | 전체 실험 기록 (실패·이력 포함) |
| `exp001_training_condition.md` | 7일차 | imgsz 640 → 1280 |
| `exp002_training_condition.md` | 7일차 | imgsz 1280 → 1920 (batch 16 → 6 동반) |
| `exp003_training_condition.md` | 7일차 | epochs 50 → 100 |
| `runs_summary.csv` | — | 전 실행 요약 (`scripts/plot_runs.py` 가 생성) |

## 하위 폴더

| 폴더 | 파일 | 내용 |
|---|---|---|
| `audit/` | `audit_summary.csv`, `audit_class_scene.csv`, `audit_issue.csv` | 전체 수량 · Class×장면 · 발견된 오류(비어 있음 = 오류 없음) |
| | `capture_group_summary.csv`, `leakage_check.csv` | 촬영 묶음별 장수·시간·장면 · Split 간 누수 점검 |
| `class5/` | `class5_review.csv`, `class5_relabel_worklist.csv` | 갈변 재검수 표 · 사람 확인 작업표 |
| | `label_changes_kimchi_v3.csv` | v3 에서 Class 5 라벨을 고친 내역 (파일별) |
| `failure/` | `failure_summary.csv` | 실패 유형 × Class 별 건수 |
| | `failure_recall_by_size.csv` | 박스 크기별 Recall (H4 근거) |
| | `failure_box_size_shift.csv` | Train vs Val 박스 크기 차이 (H1 근거) |
| `history/` | `baseline_v1_*` (3개) | 첫 Baseline (kimchi_v1) — 6일차 실패분석의 대상 |
| | `history_v2_…`, `history_v3_…` | kimchi_v2(G00 분할 수정) · v3(Class 5 라벨 개정) 학습 조건 |
| | `smoke_test.md` | 파이프라인 점검용 (성능 비교 대상 아님) |

`history/` 는 Dataset Version 마다 Val 구성이 달라 **`v4` 점수와 비교하지 않는다.** 지우지 않고 남긴 기록이다.

## 학습 실행 한눈에 (`runs_summary.csv` 요약)

| 실행 | Dataset | imgsz | epochs | mAP50-95 | 학습 곡선 |
|---|---|---:|---:|---:|---|
| `baseline_v4` (공식 Baseline) | v4 | 640 | 50 | 0.534 | `figures/runs/baseline_v4.png` |
| `exp001_v4_imgsz1280` | v4 | 1280 | 50 | 0.708 | `figures/runs/exp001_v4_imgsz1280.png` |
| `exp002_v4_imgsz1920` | v4 | 1920 | 50 | 0.758 | `figures/runs/exp002_v4_imgsz1920.png` |
| `exp003_v4_imgsz1920_epoch100` (Val 최고) | v4 | 1920 | 100 | 0.774 | `figures/runs/exp003_v4_imgsz1920_epoch100.png` |

Weight 는 `models/baseline/`, `models/improved/` 에 있다.

## 7일차 Daily Gate 에서 아직 없는 것

- `baseline_vs_improved.md`
- exp001 Confusion Matrix (`figures/` 에는 Baseline 것만 있다). 학습 곡선은 `figures/runs/exp001_v4_imgsz1280.png` 로 이미 있으나 가이드가 정한 이름(`exp001_results.png`)과 다르다.
