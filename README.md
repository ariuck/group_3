<div align="center">

# 조각김치 이물검출

**라벨을 검수하고, 작은 이물을 찾습니다.**

AI Campus · Group 3

</div>

교육용 이미지의 라벨을 직접 검수하는 도구를 만들고, 검수한 데이터로 YOLO11 객체검출 모델을 학습·평가한 팀 프로젝트입니다.

## 핵심 결과

| 검수 | 라벨 변경 | 최종 평가 |
|:---:|:---:|:---:|
| **900장** | **235장** | **0.639** |

전수 교차검수 · YOLO11s · Test 82장 · mAP50–95

![직접 개발한 라벨링 도구 — 공개용 가상 샘플 화면](subject7/docs/project/images/ui_main.png)

*직접 만든 가상 샘플로 실행한 화면입니다. 학습용 원본 사진은 공개하지 않습니다.*

## 프로젝트 구성

| 프로젝트 | 만든 것 |
|---|---|
| [**교과 7 · 라벨링 도구**](subject7/README.md) | BBox·Class 편집, 검수 기록, 품질검사·최종 데이터 생성 |
| [**교과 8 · 객체검출**](subject8/README.md) | YOLO11 학습·개선, 실패 분석, 최종 평가·웹 시연 |
| [**공동 발표자료**](presentation/README.md) | HTML 슬라이드, 발표 대본·진행표, 녹화 시연 |

## 핵심 개선

- **라벨 품질** — 원본을 보호하며 수정 이력을 남기고, 900장 전체를 서로 다른 사람이 교차검수했습니다.
- **평가 데이터** — 같은 촬영 묶음이 Train과 Val에 함께 들어가는 문제를 줄이도록 데이터를 다시 나눴습니다.
- **모델 성능** — 같은 v5 Validation에서 mAP50–95를 0.470 → 0.749로 개선했습니다. 최종 성능은 별도 Test의 0.639로 보고합니다.

남은 과제는 갈변 검출과 정상 김치에서의 오검출 평가입니다.

<details>
<summary>평가 조건·한계와 근거</summary>

- 공식 데이터 버전은 `kimchi_v5`, 최종 모델은 YOLO11s `exp050`입니다.
- Validation은 104장, Frozen Test는 82장입니다. 서로 다른 평가 역할이므로 두 점수를 직접적인 성능 개선으로 비교하지 않습니다.
- Final의 Val 0.749는 동일 조건 seed 5개 중 최고 값이며 평균은 0.739입니다. Baseline 0.470과 Final 0.749는 학습 중 best epoch 기준입니다.
- Final 확정 전에 Test 점수를 한 차례 열람한 기록이 있습니다. 평가 이력은 아래 보고서에 남겼습니다.
- 갈변의 Test Recall은 0입니다. 정상 김치 사진이 없어 정상 제품의 오검출률은 검증하지 못했습니다. 새 생산현장에 배포한 시스템은 아닙니다.
- v4 → v5 변경은 동일 사진의 중복이 아니라 **같은 촬영 묶음의 Train·Val 공유**를 줄인 것입니다. v4는 Val 132장 중 83장, v5는 Val 104장 중 6장(G00 예외)이 Train과 같은 묶음에 속합니다.

[라벨 QA](subject7/reports/qa_summary.md) · [모델 선택 근거](subject8/reports/final_model_selection.md) · [최종 Test 결과](subject8/reports/05_final/final_metrics.csv) · [평가 이력](subject8/reports/04_improvement/baseline_vs_improved.md)

</details>

## 문서 안내

[교과 7 문서](subject7/docs/README.md) · [교과 8 문서](subject8/docs/README.md) · [실험·평가 보고서](subject8/reports/README.md)

<details>
<summary>폴더 구조·문서 규칙·공개 범위</summary>

```text
group_3/
├── subject7/       라벨링 도구·검수·QA
├── subject8/       모델 학습·평가·웹 시연
└── presentation/   발표자료·대본·진행표
```

코드 설명서는 각 교과 폴더를 기준으로 `src/x.py → docs/src/x.md`처럼 같은 경로에 둡니다. 상세 사용법·정책·설계·팀 기록은 `docs/project/`, 검증 결과는 `reports/`에 모읍니다.

원본 사진·RAW·WORK·작업 중 검수표·실제 사진이 포함된 캡처와 영상은 Git에서 제외합니다. 허용된 최종 라벨·검수표·모델·기록·그래프는 각 폴더의 `.gitignore`에 따라 공유합니다. 실행에 필요한 원본 사진은 별도로 준비해야 합니다.

기술: Python · Tkinter · PyTorch · Ultralytics YOLO11 · FastAPI

[문서 작성·공유 규칙](CONTRIBUTING.md)

</details>
