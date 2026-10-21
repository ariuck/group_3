# 교과 8 · 시연 절차

[← 프로젝트 문서](README.md) · [웹 시연 설명서](../app/server.md) · [발표자료 실행](../../../presentation/README.md)

현재 시연 대상은 **`kimchi_v5` · Final `exp050` (YOLO11s · imgsz 2240)**입니다. 본편 15번에서는 녹화 영상을 재생하고, 라이브 GUI는 질문이 있을 때 부록 A17에서 엽니다. 발표 진행과 영상 파일은 발표 README를 기준으로 준비합니다.

## 준비

1. [실행 가이드](guides/training.md#6-실행-및-재현-방법)에 따라 원본 사진·환경·모델 경로를 준비합니다.
2. `subject8/`에서 가상환경의 Python으로 `app/server.py`를 실행하고 `http://127.0.0.1:8010`을 엽니다.
3. Validation 사진이 열리고 Final 모델·데이터 버전이 맞는지 확인합니다. Frozen Test·Bridge를 시연용으로 사용하지 않습니다.
4. 발표 PC에 별도로 받은 영상과 자막이 재생되는지 확인합니다. 실제 사진·영상은 Git에 올리지 않습니다.

```bash
# 저장소 루트에서
cd subject8
.venv/bin/python app/server.py
```

## 라이브 GUI에서 보여줄 순서

| 순서 | 조작 | 설명할 내용 |
|---|---|---|
| 1 | Validation 사진 선택 | 정답과 예측 BBox·Class·확신도 비교 |
| 2 | 화면 확대 | 작은 이물을 실제로 찾았는지 확인 |
| 3 | 확신도 기준 조절 | 맞힘·놓침·오검출의 변화, 운영 기준은 현장 요구로 결정 |
| 4 | Validation 일괄 채점 | 평균 점수뿐 아니라 실패 유형·Class별 결과 확인 |
| 5 | 보고서 미리보기·저장·인쇄 | 기준별 그래프·사진별 결과와 한계를 정리 |

Validation 전체 비교의 기록은 conf 0.25에서 **TP 506 · FP 31 · FN 34 · Class 틀림 1**입니다. 이 집계와 mAP는 다른 지표이므로 같은 값으로 설명하지 않습니다. [근거](../../reports/03_failure_analysis/failure_hypothesis.md)

## 후보 라벨과 사람 검수

웹 GUI는 새 사진을 입력받아 **YOLO TXT 후보 저장**을 지원합니다. 후보를 사진과 함께 교과 7 도구에서 열고 사람이 BBox·Class를 확인·수정·승인해야 정답으로 사용할 수 있습니다.

전용 배치 도구 `scripts/12_auto_label.py`와 사람 검수까지 이어지는 전체 자동화는 미완성입니다. 시연에서 후보 저장을 보여줬다는 이유로 Auto Label 전체가 완료됐다고 설명하지 않습니다. 사진·후보 TXT를 공개 경로에 올리지 않습니다.

## 터미널로 예측만 확인하기

이미 준비된 `subject8/`에서 실행합니다. 기본 예측은 Validation을 사용합니다.

```bash
.venv/bin/python scripts/08_predict_images.py --model final --limit 5
```

출력은 `runs/predict/` 아래이며, 정확한 실행별 폴더는 [예측 스크립트 설명서](../scripts/08_predict_images.md)를 봅니다. `--model final`을 사용하면 공식 Weight와 imgsz가 자동으로 정해집니다.

## 문제가 생겼을 때

| 증상 | 대응 |
|---|---|
| 사진·영상이 안 보임 | 별도로 받은 파일과 경로를 확인하고 준비한 녹화 시연으로 전환 |
| 패키지·모델 경로 오류 | 녹화 시연을 사용하고 발표 뒤 실행 가이드로 환경 확인 |
| GPU 메모리 부족·예측 지연 | 녹화 시연으로 전환; 발표 중 모델 조건을 임의로 바꾸어 성능을 주장하지 않음 |
| 검수 연계가 안 됨 | 후보 저장과 사람 승인 절차의 차이를 설명하고 미완성 범위를 명시 |

시연 중 발견한 문제는 [인수 시험 보고서](../../reports/05_acceptance/acceptance_test.md)의 재현·오류 기록에 남깁니다. 기존 보고서의 PASS·TODO를 확인 없이 바꾸지 않습니다.
