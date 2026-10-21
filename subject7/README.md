# 교과 7 · Kimchi YOLO Labeling Tool

**정답 라벨을 확인·수정하고, 검수 이력과 함께 최종 데이터로 만드는 데스크톱 도구**

[전체 프로젝트](../README.md) · [상세 사용법](docs/project/guides/labeling.md) · [코드 문서](docs/README.md) · [교과 8](../subject8/README.md)

---

## 주요 기능

- **BBox·Class 편집**: 이동·크기 조절·추가·삭제, Undo/Redo, 확대·화면 이동
- **RAW와 비교**: 원본 대비 추가·수정·삭제된 박스를 색으로 표시
- **검수 흐름 지원**: 이미지 목록·상태별 필터, 검수 기록, 단축키, 작업 이어서 시작
- **데이터 품질검사**: 이미지·라벨 짝, TXT 형식, Class·좌표 범위, 중복 BBox 확인
- **원본 보호·최종본 생성**: RAW 직접 저장 방지, WORK 저장, 완료 조건을 확인한 FINAL 생성

![설명용 가상 샘플로 실행한 라벨링 화면](docs/project/images/ui_main.png)

*설명용으로 직접 만든 가상 샘플 화면입니다. 학습용 원본 사진을 공개한 화면이 아닙니다.*

## 검수 결과

| 항목 | 결과 |
|---|---:|
| 전수 교차검수 | 900 / 900장 |
| 최종 BBox | 4,561개 (원본 4,399개) |
| 라벨이 원본과 달라진 사진 | 235장 |
| 최종 QA | FAIL 0 · REVIEW 0 |
| 실제 데이터 저장·재로드 비교 | 900 / 900장 일치 |

[QA 결과](reports/qa_summary.md) · [프로그램 테스트 결과](reports/test_report.md) · [최종본 증빙](reports/final_evidence.md) · [교과 8 인계](docs/project/handoff/subject08_handoff.md)

검수 상태의 `수정 완료` 장수와 실제 라벨 변경 장수는 다릅니다. 상태는 사람이 선택할 수 있으며, 차이 9장의 설명은 QA 보고서에 남겼습니다.

## 빠른 시작

아래는 **Linux / WSL, 저장소 루트(`group_3/`) 기준**입니다. Windows 설치·실행과 전체 조작법은 [상세 가이드](docs/project/guides/labeling.md)에 있습니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r subject7/requirements.txt
cd subject7
../.venv/bin/python main.py
```

- 사진과 원본 라벨은 `subject7/data/raw/`에 별도로 준비합니다.
- Tkinter가 없으면 Ubuntu에서 `sudo apt install python3-tk`로 설치합니다.
- 다른 PC에서 기존 검수 작업을 복원할 때는 [restore_from_final 설명서](docs/tools/restore_from_final.md)를 따릅니다.

## 사용 흐름

**폴더 열기 → BBox·Class 확인·수정 → 검수 기록 → WORK 저장 → QA → FINAL 생성**

RAW는 읽기 전용으로 유지합니다. 정상 여부를 판단하기 어려운 사진은 `수정 필요`로 남겨 재검수하며, 자동 저장된 후보를 바로 최종 정답으로 취급하지 않습니다.

## 구조와 문서

```text
subject7/
├── main.py                 프로그램 시작
├── configs/                Class 설정
├── src/                    UI·BBox·YOLO 입출력·검수 기록·QA
├── tools/                  라벨 취합·복원·최종본·보고서 도구
├── tests/                  로직·UI·도구 테스트
├── docs/
│   ├── main.md             main.py 설명서
│   ├── src/ · tools/ · tests/   같은 경로의 Python 설명서
│   └── project/            사용법·기준서·설계·팀 운영·인계
├── data/                   RAW·WORK·FINAL (사진 제외)
├── manifests/              검수표 틀·작업 기록
└── reports/                QA·테스트·최종본 증빙
```

| 목적 | 문서 |
|---|---|
| 설치·조작·최종본 생성 | [상세 사용 가이드](docs/project/guides/labeling.md) |
| Class·BBox·검수표 작성 기준 | [프로젝트 문서](docs/project/README.md) |
| 파일별 코드 이해·테스트 실행 | [코드 문서 목차](docs/README.md) |
| 모델 학습으로 이어가기 | [교과 8 인계](docs/project/handoff/subject08_handoff.md) |

## 주의사항과 한계

- 원본 사진·RAW·WORK·작업 중 검수표는 Git에 없습니다. 최종 라벨·`data/final/검수표.csv`·`classes.txt`는 공유되며 원본 사진과 함께 복원합니다.
- 정상 김치 사진은 0장으로, 정상 제품에서의 오검출 평가를 지원할 데이터가 부족합니다.
- 검수표의 일부 확인 칸은 상태 기록으로 갈음했습니다. 자동 시험·실데이터 점검·사람 확인의 근거는 [테스트 보고서](reports/test_report.md)에 구분해 두었습니다.
- WSL 한글 입력·폴더 끌어다 놓기 등 환경에 따른 제약은 [상세 가이드](docs/project/guides/labeling.md#16-알려진-제한사항)를 참고합니다.
