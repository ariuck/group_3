# 교과 8 · 인수 점검 및 종료 검토

[프로젝트 종료 현황](../../../PROJECT_STATUS.md) · [보고서 목차](../README.md)

**교과 7·8 종료일: 2026-10-21.** 현재는 발표자료를 보완하고 있습니다. 이 문서는 종료 시점의 제공 기능과 검증 범위를 기록합니다.

## 1. 점검 기준과 결과

| 구분 | 내용 |
|---|---|
| 이번 점검일 | 2026-10-21 |
| 대상 | `kimchi_v5` · Final `exp050_v5_s_imgsz2240_aug_seed2` |
| 방법 | 현행 자동 점검 재실행 + 기존 보고서 대조 + 합성 입력 시험 + 로컬 영상 구조 점검 |
| 이번에 하지 않은 것 | 재학습·Frozen Test 재평가·라벨 및 데이터 분할 변경 |
| 자동 점검 원본 | [acceptance_check.csv](acceptance_check.csv) |

| PASS | FAIL | TODO | MANUAL | INFO | NOT_DELIVERED |
|---:|---:|---:|---:|---:|---:|
| 85 | **0** | 0 | 5 | 2 | 1 |

- **PASS**: 해당 자동 검사 통과. 코드 존재·파일 해시·파일 준비 등 각 행에 적힌 범위만 보장합니다.
- **FAIL / TODO**: 검사 실패 / 필요한 파일 부재. 이번 실행은 둘 다 0입니다.
- **MANUAL**: 자동으로 판정할 수 없는 동작·이력·독립 재현. 기존 확인 기록과 미확인 범위는 3장에서 구분합니다.
- **INFO**: 구형 경로·후속 참고 문서 등 참고 사항입니다.
- **NOT_DELIVERED**: 전용 Auto Label 배치 도구 1개 항목입니다. 미제공 기능을 PASS로 바꾸지 않았습니다.

따라서 `TODO 0`을 모든 초기 계획의 구현 완료나 모든 수동 시험의 통과로 해석하지 않습니다.

## 2. 확인된 제공 결과

| 영역 | 확인된 내용 | 근거 |
|---|---|---|
| 교과 7 데이터 | 900장 전수 교차검수·최종 BBox 4,561개·라벨 변경 235장·QA FAIL 0 | [QA Summary](../../../subject7/reports/qa_summary.md) |
| 분할 | Train 558 · Val 104 · Test 82 · 미사용 Bridge 156, 역할 사이 동일 이미지 중복 없음 | [데이터 요약](../01_data/dataset_summary.csv) · [분할 정책](../../docs/project/split_policy.md) |
| 모델 | 보관 Weight와 조건 기록의 해시, 공식 Final과 모델 선택 근거 일치 | [모델 선택 보고서](../final_model_selection.md) · [자동 점검 CSV](acceptance_check.csv) |
| 최종 성능 | Test P 0.868 · R 0.744 · mAP50 0.726 · mAP50–95 0.639 | [기록된 Test 결과](../05_final/final_metrics.csv) |
| 예측 화면 | 2026-10-20 Val 104장 전체 예측·Class별 화면의 사람 확인 기록 있음 | [이전 보고서 4장](history/pre_closeout_acceptance_test.md#4-inference--auto-label) |
| GUI 후보 TXT | `app/static/app.js`의 `saveTxt()` 구현·버튼 확인, 합성 입력 3개 시험 통과 | [서버 설명서](../../docs/app/server.md) · 실제 함수 실행 |
| 시연 영상 | 로컬 2개·처음/마지막 프레임 디코딩 통과 | `presentation/private/videos/` — Git 제외, 파일명·영상은 공개하지 않음 |
| 코드·환경 | Python 문법, 학습·추론·FastAPI 의존성, Git 추적 사진·Weight 경로 점검 통과 | [자동 점검 CSV](acceptance_check.csv) |

검사 코드의 변경은 [회귀 테스트](../../docs/tests/test_qa_acceptance_check.md) 5개로 확인했습니다. 교과 7의 화면 없는 기존 테스트도 77개 통과했습니다. 전체 GUI 시험을 새로 수행한 결과는 아닙니다.

<details>
<summary>자동 판정 밖의 이력·추가 확인 기록</summary>

종료 시점 후보 TXT 전체 흐름과 다른 팀원의 독립 재현은 별도 확인 기록 없음으로 정리했습니다. 현재 발표 보완을 위해 추가 수행해야 하는 작업 목록은 아닙니다.

| 자동 결과 | 종료 검토 |
|---|---|
| G00 촬영 묶음 공유 | 의도한 분할 예외이며 정책·기존 사람 확인 기록에 명시됨. 같은 사진 중복과 다른 문제 |
| Frozen Test 사전 열람 | 2026-10-16 열람 예외 기록 있음. 잔여 로그 검사로 삭제된 이력이나 미열람을 증명할 수 없음 |
| 예측 화면의 동작 | 2026-10-20 Val 104장 확인 기록을 보존. 이번 점검에서는 모델 예측·화면 시험을 재실행하지 않음 |
| 후보 TXT → 교과 7 수정·승인 전체 흐름 | 도구별 기능은 있으나 전체 흐름의 독립 시험 기록 미확인 |
| 다른 팀원의 새 환경 재현 | 별도 재현 결과가 문서에 기록되어 있지 않음 |

이번 GUI 저장 함수 시험은 정상 예측 1건의 YOLO 정규화 좌표, 예측 0건의 빈 TXT, 예측 결과 없음 처리를 합성 데이터로 검사했습니다. 실제 브라우저 다운로드·사람 승인 전체를 통과했다고 확장하지 않습니다.

</details>

## 4. 초기 계획과 종료 시점의 차이

- **전용 배치 Auto Label**: `scripts/12_auto_label.py`·`src/auto_labeler.py`는 제공되지 않았습니다. 웹 GUI의 후보 TXT 저장과 분리해 기록합니다.
- **초기 `demo/` 모음**: 세 폴더는 비어 있습니다. 현재 발표 준비는 `presentation/README.md`의 영상·사진 경로를 사용하므로, 이 폴더가 비었다는 이유만으로 현재 GUI·녹화 시연을 미구현으로 판정하지 않습니다.
- **교과 14**: 모델·대상·방향이 정해지지 않았습니다. 기존 인계 문서는 후속 활용 참고이며, 교과 7·8 종료의 필수 합격 조건으로 검사하지 않습니다.

## 5. 알려진 모델 한계와 과거 기록

갈변 Test Recall 0, 정상 김치 이미지 부재, 소품 공유·적은 Class별 표본, G00 예외와 Test 사전 열람 이력을 남깁니다. [Class별 결과](../05_final/final_class_metrics.csv) · [평가 이력](../04_improvement/baseline_vs_improved.md)

2026-10-20의 원본 자동 점검(PASS 83 · TODO 4 · MANUAL 4)과 당시 사람 확인을 반영한 보고서는 보존했습니다. 과거 값과 이번 값을 섞어 합격 건수를 계산하지 않습니다.

[과거 자동 점검 원본](history/2026-10-20_acceptance_check.csv) · [종료 정리 직전 보고서](history/pre_closeout_acceptance_test.md)

## 다시 점검하기

`subject8/`에서 실행합니다. 기본 실행은 현행 CSV를 갱신하며, 과거 기록은 `history/`에 보존합니다.

```bash
.venv/bin/python scripts/qa_acceptance_check.py
.venv/bin/python scripts/qa_acceptance_check.py --output /tmp/group3_acceptance_review.csv
.venv/bin/python -m unittest discover -s tests -p test_qa_acceptance_check.py -v
```

모델을 새로 학습하거나 Test를 재평가하는 명령이 아닙니다. 영상 준비 여부는 해당 PC의 로컬 파일 상태에 따라 달라질 수 있습니다.
