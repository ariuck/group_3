# 교과 8 · 조각김치 이물검출

**YOLO11n Baseline에서 YOLO11s Final까지, 데이터 분할·실패 분석·개선 실험·최종 평가**

[전체 프로젝트](../README.md) · [실행·실험 가이드](docs/project/guides/training.md) · [코드 문서](docs/README.md) · [보고서](reports/README.md) · [모델 목록](models/README.md)

---

## 결과 요약

공식 데이터 버전은 **`kimchi_v5`**, 최종 모델은 **`exp050_v5_s_imgsz2240_aug_seed2`**입니다.

| 평가 | 대상 | mAP50–95 | 용도 |
|---|---|---:|---|
| Baseline Validation | YOLO11n · imgsz 640 | 0.470 | 개선 비교의 출발점 |
| Final Validation | YOLO11s · imgsz 2240 | 0.749 | 후보·seed 선택 결과 |
| **Final Frozen Test** | **YOLO11s · 82장** | **0.639** | **선택된 모델의 최종 성능** |

![핵심 실험의 Validation 비교와 별도 Frozen Test 결과](reports/figures/comparison/portfolio_summary.svg)

Validation 수치는 같은 v5 Val 104장의 **학습 중 best epoch** 기준입니다. 재평가 CSV의 Baseline 0.471과는 측정 시점이 다릅니다. Final의 동일 조건 seed 5개 평균은 0.739이며, 표의 0.749는 최고 seed 값입니다. Final 확정 전 Test 점수를 한 번 열람한 기록은 [평가 이력](reports/04_improvement/baseline_vs_improved.md)에 있습니다.

근거: [모든 학습 실행](reports/runs_summary.csv) · [모델 선택 근거](reports/final_model_selection.md) · [최종 Test CSV](reports/05_final/final_metrics.csv) · [Class별 Test CSV](reports/05_final/final_class_metrics.csv)

## 데이터와 실험 흐름

**교과 7 최종본 → 데이터 점검 → 촬영 묶음 기반 분할 → Baseline → 실패 분석 → 개선 실험 → Final → Test**

| Train | Validation | Frozen Test | Bridge Holdout |
|---:|---:|---:|---:|
| 558장 | 104장 | 82장 | 156장 |

Bridge는 교과 14용으로 남겨 두었으며 교과 8 학습·선택·평가에 사용하지 않았습니다. 원래의 train/validation 구분과 교과 8의 역할 분할은 다릅니다. [분할 정책](docs/project/split_policy.md) · [v5 분할 기준과 한계](docs/project/kimchi_v5_split.md)

## 빠른 시작

아래는 **Linux / WSL, 저장소 루트(`group_3/`) 기준**입니다. 원본 사진을 `subject7/data/raw/`에 별도로 준비한 뒤 진행합니다. 기존 환경을 포함한 자세한 준비 절차는 [실행·실험 가이드](docs/project/guides/training.md#6-실행-및-재현-방법)를 봅니다.

```bash
cd subject8
python3 scripts/00_setup.py
.venv/bin/python scripts/01_check_environment.py
.venv/bin/python scripts/08_predict_images.py --model final --limit 5
```

모델은 저장소의 `models/`에 있어 준비된 환경에서는 재학습 없이 예측할 수 있습니다. `--model final`은 공식 모델과 imgsz 2240을 자동으로 선택합니다.

### 웹 시연

위 데이터·환경 준비가 끝난 `subject8/`에서 실행합니다.

```bash
.venv/bin/python app/server.py
```

브라우저에서 **http://127.0.0.1:8010**을 엽니다.

- Validation 사진의 정답·예측 비교, 확대, 확신도 기준 조절
- Validation 일괄 채점과 HTML 보고서·인쇄
- 새 사진 입력과 YOLO TXT 후보 저장 (사람 검수 후 확정)

[시연 절차](docs/project/demo_procedure.md) · [서버 설명서](docs/app/server.md) · [보고서 설명서](docs/app/report.md)

### 학습과 평가는 상세 가이드에서

학습은 GPU·시간이 필요한 작업입니다. 환경 확인, 분할, Baseline·개선 실험 명령은 [실행·실험 가이드](docs/project/guides/training.md)에 정리했습니다. Frozen Test를 재학습 점검용으로 반복 실행하거나, Bridge 평가를 교과 8 과정에서 실행하지 않습니다.

## 구현 상태와 한계

| 항목 | 현재 상태 |
|---|---|
| 데이터 점검·분할·Baseline·개선 실험 | 결과와 조건 기록 있음 |
| Final 선택·Frozen Test | `exp050` 확정·정식 평가 결과 있음 |
| 웹 시연·보고서·후보 TXT 저장 | 구현됨 |
| 전용 Auto Label 배치 도구·사람 검수 연계 | 미완성 (`12_auto_label.py` 없음) |
| 인수 시험·다른 팀원 재현 | [Acceptance Test](reports/05_acceptance/acceptance_test.md)에 완료·TODO·수동 확인 구분 |

**갈변(Class 5)의 Test Recall은 0**입니다. 정상 김치 이미지도 없어 정상 제품의 오검출률은 확인하지 못했습니다. 평가는 새 현장의 처음 보는 물체를 보장하지 않으며, Class별 표본 수와 촬영 소품 공유에 따른 한계가 있습니다. [상세 한계·후속 과제](docs/project/handoff/subject14_handoff.md)

## 구조와 문서

```text
subject8/
├── app/                    FastAPI 서버·보고서·브라우저 화면
├── src/                    학습·평가·추론 공통 모듈·모델 등록부
├── scripts/                준비·학습·평가·실패 분석·그래프 생성
├── configs/                데이터·모델 설정
├── docs/
│   ├── app/ · src/ · scripts/   같은 경로의 Python 설명서
│   ├── manifests/          분할 분석 도구의 미러 설명서
│   └── project/            상세 가이드·정책·과정·시연·인계
├── manifests/              데이터 역할·촬영 묶음·분할 기록
├── models/                 공식·개선·과거 버전 모델
├── runs/                   실행별 학습 조건·로그·그래프
└── reports/                데이터·실험·최종 평가·인수 시험
```

[프로젝트 문서 목차](docs/project/README.md) · [보고서 목차](reports/README.md) · [교과 14 인계](docs/project/handoff/subject14_handoff.md) · [공동 발표자료](../presentation/README.md)
