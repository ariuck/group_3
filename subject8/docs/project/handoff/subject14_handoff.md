# 후속 활용 참고 · 현재 김치 모델과 데이터

[프로젝트 종료 현황](../../../../PROJECT_STATUS.md) · [프로젝트 문서](../README.md) · [교과 8 README](../../../README.md)

**교과 7·8은 2026-10-21 종료했습니다. 교과 14의 대상·모델·진행 방향은 미정입니다.** 다른 검출 모델이나 데이터로 전환할 수 있으며, 현재 김치 모델의 승계를 전제로 하지 않습니다.

이 문서는 기존 `subject14_handoff.md` 경로에 현재 결과와 재현 경로를 보존하는 참고 자료입니다. 후속 교과의 필수 인계·합격 조건이나 확정 일정이 아닙니다.

## 1. 현재 프로젝트가 남긴 결과

| 항목 | 결과·위치 |
|---|---|
| Dataset Version | `kimchi_v5` — Train 558 · Val 104 · Frozen Test 82 · 미사용 Bridge Holdout 156 |
| Final Model | `exp050_v5_s_imgsz2240_aug_seed2` · YOLO11s · imgsz 2240 |
| 공식 Weight | `models/final/final_best.pt` · [모델 목록](../../../models/README.md) |
| Validation | mAP50–95 0.749 (같은 조건 seed 5개 중 최고, 평균 0.739) |
| Frozen Test | mAP50–95 0.639 · P 0.868 · R 0.744 · mAP50 0.726 (82장·432박스) |
| 선택 근거 | [final_model_selection.md](../../../reports/final_model_selection.md) |
| 실행·재현 | [실행·실험 가이드](../guides/training.md) · [인수 점검](../../../reports/05_acceptance/acceptance_test.md) |

현재 모델의 성능을 설명할 때는 Test 0.639를 사용합니다. Final 확정 전 Test 점수를 한 번 열람한 기록이 있으므로 미열람을 전제로 한 평가라고 설명하지 않습니다. [평가 이력](../../../reports/04_improvement/baseline_vs_improved.md)

## 2. Bridge Holdout의 의미

Bridge 156장(G10·G11·G12 + G00 6장)은 교과 8 학습·튜닝·선택·Frozen Test에 사용하지 않은 보존 데이터입니다. `configs/dataset.yaml`에 넣지 않았습니다.

- 이 김치 데이터와 모델을 후속 작업에서도 사용한다면, 새 계획에 따라 비교·평가 자료로 활용할 수 있습니다.
- 교과 14의 첫 평가를 반드시 이 모델과 Bridge로 해야 한다는 뜻은 아닙니다. 대상·모델·데이터가 달라지면 평가 체계도 새로 정해야 합니다.
- Bridge도 Train과 같은 촬영 날짜·소품을 공유하므로 완전히 새로운 현장 데이터로 간주하지 않습니다.
- 기존 평가 도구는 [`17_evaluate_bridge.py`](../../scripts/17_evaluate_bridge.md)에 있습니다. `--subject14`는 기존 보호 플래그이며 사용 계획이 확정됐다는 표시가 아닙니다. 이번 종료 점검에서 실행하지 않았습니다.

[분할 정책](../split_policy.md) · [v5 분할 기준](../kimchi_v5_split.md)

## 3. 현재 모델을 재사용할 경우 알아둘 한계

| 항목 | 현재 확인된 한계 |
|---|---|
| 갈변 | Test Recall 0.00 · mAP50–95 0.007. 작은 갈색 반점과 학습 데이터의 큰 갈변 사이 차이 |
| 나뭇잎·종이 | Test Precision 약 0.37로 오검출이 많음 |
| 정상 김치 | Negative 이미지가 0장이라 정상 제품의 오검출률 미검증 |
| 새 물체·새 환경 | 같은 소품·촬영 날짜 공유로, 처음 보는 소품·현장 성능을 보장하지 않음 |
| 적은 표본 | 갈변·벌레 등의 평가 박스 수가 적어 작은 점수 차이 해석에 주의 |
| 검출 대상 | 현재 Class ID 0~6 기준. 머리카락·실 등 범위 밖 이물은 대상이 아님 |
| 실행 조건 | imgsz 2240·기록된 장치 조건의 결과. 다른 모델·해상도·장치에 그대로 적용하지 않음 |

[Class별 Test 결과](../../../reports/05_final/final_class_metrics.csv) · [실패 분석](../../../reports/03_failure_analysis/failure_hypothesis.md)

## 4. 현재 구현과 제공 범위

웹 GUI는 정답·예측 비교, 확신도 조절, Val 일괄 채점, 보고서, 후보 YOLO TXT 저장을 지원합니다. 후보는 사람 확인·수정·승인 후에 정답으로 사용해야 합니다.

전용 Auto Label 배치 도구와 전체 사람 검수 흐름의 독립 시험은 완료로 기록하지 않습니다. 정확한 미제공·미확인 상태는 [종료 현황](../../../../PROJECT_STATUS.md)을 봅니다.

## 5. 후속 방향이 정해진 뒤 검토할 항목

다음은 확정 일정이 아닌 참고 항목입니다.

1. 검사 대상·모델·데이터·Class 정의와 놓침·오검출의 허용 기준을 새로 정합니다.
2. 현재 데이터나 Weight를 이어 쓸 때만 기존 Version·Class·평가 이력을 함께 가져갑니다. 다른 모델로 전환하면 호환성을 별도 검토합니다.
3. 새로운 데이터의 분할·Validation·Test 역할을 정하고, 이미 사용한 Test를 모델 튜닝 기준으로 반복 사용하지 않습니다.
4. 기존 사진의 공개 제한을 유지합니다. 원본 사진·실제 사진이 포함된 캡처·영상은 공개 Git에서 제외합니다.

현재 진행 중인 후속 학습·추가 실험·Bridge 평가를 의미하지 않습니다.
