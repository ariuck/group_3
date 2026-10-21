# 교과 8 · 결과 보고서

[교과 8 README](../README.md) · [프로젝트 종료 현황](../../PROJECT_STATUS.md) · [모델 목록](../models/README.md)

**교과 7·8은 2026-10-21 종료했습니다.** 아래는 개발 중인 작업 목록이 아니라, 완료된 실험·검증과 종료 시점의 제공 범위를 확인하는 자료입니다. 현재는 발표자료를 보완합니다.

## 먼저 볼 결과

| 확인할 내용 | 근거 |
|---|---|
| 최종 모델과 선택 이유 | [final_model_selection.md](final_model_selection.md) |
| 최종 Test 성능 | [전체 지표](05_final/final_metrics.csv) · [Class별 지표](05_final/final_class_metrics.csv) |
| 개선 과정·모델의 한계 | [Baseline vs Final](04_improvement/baseline_vs_improved.md) · [실험 기록 CSV](04_improvement/experiment_log.csv) |
| 종료 점검·미제공·미확인 범위 | [인수 점검 보고서](05_acceptance/acceptance_test.md) |

## 결과의 위치

단계 폴더는 공식 버전 `kimchi_v5` 기준입니다. 과거 버전은 `history/<Version>/`에 보존하며, 서로 다른 Val 구성의 점수를 직접 비교하지 않습니다.

| 폴더·파일 | 담긴 결과 |
|---|---|
| [`01_data/`](01_data/) | 데이터 수량·무결성·촬영 묶음·라벨 수정·v4→v5 분할 분석 |
| [`02_baseline/`](02_baseline/) | 공식 Baseline 조건·Validation 성능·Class별 성능 |
| [`03_failure_analysis/`](03_failure_analysis/) | Baseline·Final 실패 유형·크기별 Recall·원인 가설과 검증 |
| [`04_improvement/`](04_improvement/) | 실험 조건·판정·후보 비교·실패한 개선 시도 |
| [`05_final/`](05_final/) | Final `exp050`의 Frozen Test 82장 결과 |
| [`05_acceptance/`](05_acceptance/) | 현행 인수 점검·종료 검토와 과거 원본 기록 |
| [`runs_summary.csv`](runs_summary.csv) | 버전별 전체 학습 실행 요약 |
| [`history/`](history/) | 지난 Dataset Version의 결과·초기 Smoke Test |
| [`figures/`](figures/) | 학습 곡선·Class별 결과·비교 그래프 |

### 05_acceptance · 종료 점검

| 파일 | 내용 |
|---|---|
| [`acceptance_test.md`](05_acceptance/acceptance_test.md) | 2026-10-21 인수 점검·종료 검토. 제공 기능·예외·미제공·미확인을 구분 |
| [`acceptance_check.csv`](05_acceptance/acceptance_check.csv) | 현행 코드로 다시 실행한 자동 점검 원본 |
| [`history/`](05_acceptance/history/) | 과거 CSV와 종료 정리 직전 보고서 보존 |

자동 FAIL은 0건입니다. `MANUAL`과 `NOT_DELIVERED`는 PASS로 바꾸지 않았으며, 교과 14 계획의 확정을 완료 조건으로 삼지 않습니다. 자세한 판정 범위는 인수 보고서를 봅니다.

### 성능을 읽는 기준

- Baseline Val 0.470 → Final Val 0.749는 같은 v5 Val 104장의 학습 중 best epoch 기준입니다. Baseline 재평가 CSV의 0.471과는 측정 시점이 다릅니다.
- 대외 최종 성능은 별도 Test의 mAP50–95 **0.639**입니다. 갈변 Test Recall은 0이며, 평가 예외·데이터 한계를 함께 설명합니다.
- 타일링 실험은 원본 이미지 단위로 합쳐 채점한 결과를 비교합니다. 자세한 조건과 seed 평균은 모델 선택 보고서를 따릅니다.

[포트폴리오 요약 그래프](figures/comparison/portfolio_summary.svg) · [모델별 그래프·Weight](../models/README.md)

요약 그래프는 `subject8/`에서 `python scripts/plot_portfolio.py`로 기존 CSV만 읽어 다시 만들 수 있습니다. 후속 과제의 모델·대상·진행 방향은 미정이며, [기존 참고 문서](../docs/project/handoff/subject14_handoff.md)는 현재 김치 프로젝트의 기록으로만 보존합니다.
