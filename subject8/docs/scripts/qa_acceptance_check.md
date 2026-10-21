# `scripts/qa_acceptance_check.py`

> 교과 8의 기록된 데이터·모델·평가·코드·로컬 시연 준비를 점검합니다. 모델 학습·추론·Frozen Test 재평가는 실행하지 않습니다.

[코드 보기](../../scripts/qa_acceptance_check.py) · [인수 보고서](../../reports/05_acceptance/acceptance_test.md) · [종료 현황](../../../PROJECT_STATUS.md)

## 실행

`subject8/`의 준비된 환경에서 실행합니다.

```bash
.venv/bin/python scripts/qa_acceptance_check.py
.venv/bin/python scripts/qa_acceptance_check.py --output /tmp/acceptance_review.csv
```

기본 출력은 `reports/05_acceptance/acceptance_check.csv`입니다. `--output`으로 다른 파일에 기록하면 기존 CSV를 보존할 수 있습니다. 과거 원본은 `reports/05_acceptance/history/`에 보존합니다. FAIL이 있으면 종료 코드 1이며, FAIL 0이 모든 수동 시험·미제공 기능의 통과를 의미하지는 않습니다.

## 결과 상태

| 상태 | 뜻 |
|---|---|
| PASS | 각 행에 적힌 자동 검사 통과 |
| FAIL | 검사 실패·필수 구현 부재·실행 오류 |
| TODO | 필요한 파일이 없어 해당 검사를 완료하지 못함 |
| MANUAL | 자동 판정 불가·동작·과거 이력·독립 재현 등 별도 근거 필요 |
| INFO | 구형 경로·후속 참고 등 안내 |
| NOT_DELIVERED | 종료 시점 제공하지 않은 기능. PASS로 계산하지 않음 |

## 주요 검사

| 함수 | 검사 범위 |
|---|---|
| `check_dataset()` | Version·역할별 수량·동일 이미지 중복·Class·촬영 묶음 예외·Test 보호와 Bridge 사용 흔적 |
| `check_model()` | 보관 Weight·학습 조건·해시·공식 Final·선택 근거 |
| `check_evaluation()` | 기존 평가 CSV·실패 분석·실험 기록·Final의 모델·장수 |
| `check_use()` | 예측 코드·GUI `saveTxt()`와 버튼·배치 도구 제공 여부·로컬 발표 영상·구형 demo 경로 |
| `check_env()` | src·scripts·app 문법·학습/추론/웹 의존성·Git 추적 파일·독립 재현 기록 안내 |
| `main(argv)` | 결과 초기화·검사 실행·CSV 출력·상태별 집계 |

## 판정의 한계

- GUI 저장의 PASS는 코드·버튼 존재를 확인한 것이며 실제 브라우저 다운로드·사람 승인 전체 흐름의 PASS가 아닙니다.
- 영상 준비 PASS는 로컬 영상 파일 수·확장자·0바이트 여부입니다. 이번 종료 검토에서 별도로 처음·마지막 프레임을 디코딩한 결과는 인수 보고서에 기록했습니다.
- Test 잔여 로그·보호 코드는 사전 미열람을 증명하지 못합니다. 실제 사전 열람 예외를 문서에 보존합니다.
- 후속 참고 문서는 INFO이며 교과 14의 모델·대상·방향 확정을 완료 조건으로 검사하지 않습니다.
- `rows.clear()`로 같은 프로세스의 반복 실행 시 결과 중복을 막습니다. [회귀 테스트](../tests/test_qa_acceptance_check.md) 5개가 GUI 경로·배치 분리·영상 경로·출력 보존을 검사합니다.

의존성: Python 표준 라이브러리, `src`의 설정·모델 등록부 및 설치된 학습·추론·웹 패키지. 원본 사진을 새로 예측하거나 외부로 전송하지 않습니다.
