# 교과 8 · 프로젝트 문서

[← 문서 목차](../README.md) · [교과 8 README](../../README.md) · [결과 보고서](../../reports/README.md)

코드 한 파일의 설명서는 `docs/app/`·`docs/src/`·`docs/scripts/` 등에 같은 경로로 있습니다. 이 폴더는 실행 가이드·분할 정책·실험 운영·시연·인계 문서를 모읍니다.

| 분류 | 읽을 문서 |
|---|---|
| **실행·재현** | [실행·실험 상세 가이드](guides/training.md) — 환경·데이터 준비·학습·예측·결과 해석 |
| **현재 분할 기준** | [분할 정책](split_policy.md) · [kimchi_v5 분할 기준](kimchi_v5_split.md) |
| **분할 작업·과정** | [수동 분할 가이드](manual_split_guide.md) · [데이터 점검·분할 과정](process/dataset_audit_and_split.md) |
| **실험 운영** | [실험 인수인계·분산 실험 기록](experiment_handoff.md) |
| **시연** | [현행 시연 절차](demo_procedure.md) — 웹 GUI·녹화 시연·후보 라벨 검수 |
| **후속 교과 인계** | [교과 8 → 교과 14](handoff/subject14_handoff.md) — Final·Bridge·한계·재현 절차 |

실험의 성능·판정·최종 평가 결과는 [`reports/`](../../reports/README.md), 공식 모델의 실제 실행 이름은 [`src/registry.py`](../../src/registry.py)를 기준으로 확인합니다. 과거 Dataset Version의 결과는 `reports/history/`에 보존합니다.
