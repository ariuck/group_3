# group_3 — 조각김치 이물검출

AI Campus 3조의 교과 7·8 프로젝트입니다. 교육용 조각김치 이미지의 라벨을 검수하고, 검수한 데이터로 YOLO 객체검출 모델을 학습·평가합니다.

**라벨 검수 → 데이터 분할 → 모델 학습·개선 → 최종 평가 → 발표·후속 교과 인계**

## 프로젝트 구성

| 구분 | 주요 내용 | 바로가기 |
|---|---|---|
| **교과 7 · 라벨링 도구** | BBox·Class 수정, 900장 교차검수, 최종 데이터 생성·품질검사 | [소개·설치·사용법](subject7/README.md) |
| **교과 8 · 객체검출** | YOLO11n Baseline → YOLO11s Final, 실패 분석·개선 실험·최종 평가, 웹 시연 | [소개·실행·재현 방법](subject8/README.md) |
| **공동 발표자료** | 교과 7·8 통합 HTML 발표자료, 발표 대본·진행표 | [발표 준비·실행 방법](presentation/README.md) |

교과 8의 최종 모델은 **YOLO11s (`exp050`, `kimchi_v5`)**입니다. Frozen Test 82장의 mAP50–95는 **0.639**이며, 갈변 검출 등 남은 한계는 [최종 모델 선택 근거](subject8/reports/final_model_selection.md)와 [최종 평가 결과](subject8/reports/05_final/final_metrics.csv)에서 확인할 수 있습니다.

## 처음 시작하기

- **라벨링 도구 실행**: [교과 7 설치 안내](subject7/README.md#4-설치)를 따른 뒤 `subject7/`에서 `python main.py`를 실행합니다.
- **모델 예측·웹 시연**: [교과 8 실행 및 재현 방법](subject8/README.md#6-실행-및-재현-방법)에서 환경과 데이터를 준비합니다. 웹 시연은 `subject8/`에서 가상환경의 Python으로 `app/server.py`를 실행합니다.
- **발표자료 보기**: `presentation/index.html`을 브라우저로 엽니다. 사진·영상은 별도로 받아야 하며, 발표 서버 실행 방법은 [발표 README](presentation/README.md)에 있습니다.

> 원본 사진과 개인 가상환경은 Git에 포함되지 않습니다. 저장소를 내려받은 뒤 각 교과의 준비 안내를 확인해 주세요.

## 폴더와 문서 구조

```text
group_3/
├── README.md             전체 프로젝트 안내
├── subject7/             라벨링 도구·검수 데이터·품질검사
│   ├── src/              프로그램 코드
│   ├── tests/ · tools/   테스트·데이터 처리 도구
│   ├── docs/             코드 경로를 따르는 설명서 + project/ 문서
│   └── reports/          품질검사·테스트 결과
├── subject8/             객체검출 학습·평가·웹 시연
│   ├── src/ · scripts/   공통 모듈·단계별 실행 코드
│   ├── app/              웹 시연 프로그램
│   ├── docs/             코드 경로를 따르는 설명서 + project/ 문서
│   └── reports/ · models/ · runs/   보고서·모델·실험 기록
└── presentation/         통합 발표자료·대본·진행표
```

코드 설명서는 **각 교과 폴더를 기준으로 같은 경로**에 둡니다. 코드 파일의 확장자를 `.md`로 바꾸고 앞에 `docs/`를 붙입니다.

| 코드 | 대응 설명서 |
|---|---|
| `subject7/main.py` | `subject7/docs/main.md` |
| `subject7/src/ui/main_window.py` | `subject7/docs/src/ui/main_window.md` |
| `subject8/scripts/00_setup.py` | `subject8/docs/scripts/00_setup.md` |
| `subject8/app/server.py` | `subject8/docs/app/server.md` |

기준서·설계·회의록·운영 기록 등 코드 파일에 직접 대응하지 않는 문서는 각 교과의 **`docs/project/`**에 모읍니다. 실험·검증 결과는 **`reports/`**에 둡니다.

문서 목차: [교과 7](subject7/docs/README.md) · [교과 8](subject8/docs/README.md) · 결과 보고서: [교과 8](subject8/reports/README.md)

## 데이터와 공유 범위

- 교육용으로 가상 생성된 조각김치 데이터를 사용합니다. 실제 생산라인에서 취득한 데이터로 표현하지 않습니다.
- **원본 사진·실제 사진이 포함된 캡처·영상은 공개 Git에 올리지 않습니다.** 발표용 사진·영상은 `presentation/private/`에 별도로 보관합니다.
- 최종 라벨·허용된 검수표·모델·학습 기록·그래프는 각 폴더의 `.gitignore` 규칙에 따라 공유합니다. RAW·WORK와 작업 중 검수표는 Git에서 제외됩니다.
- 교과 7·8은 서로의 데이터 경로를 사용합니다. `subject7/`·`subject8/` 이름과 상대 위치를 유지합니다.
