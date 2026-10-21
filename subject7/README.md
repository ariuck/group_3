# 교과 7 · 라벨링 도구

**2026-10-21 교과 7·8 종료. 현재는 발표자료를 보완합니다.** [종료 현황](../PROJECT_STATUS.md)

**라벨을 고치고, 검수 이력을 남기고, 최종 데이터로 만듭니다.**

[전체 프로젝트](../README.md) · [상세 사용법](docs/project/guides/labeling.md) · [코드 설명서](docs/README.md)

![라벨링 도구 — 공개용 가상 샘플 화면](docs/project/images/ui_main.png)

*직접 만든 가상 샘플로 실행한 화면입니다. 학습용 원본 사진은 공개하지 않습니다.*

## 주요 기능

- **편집** — BBox 이동·크기 조절·추가·삭제, Class 변경, Undo/Redo
- **검수** — RAW 비교, 이미지 목록·상태별 필터, 검수 기록·이어 하기
- **품질검사** — 이미지·라벨 짝, TXT 형식, Class·좌표 범위 확인
- **최종본 생성** — RAW 보호, WORK 저장, 완료 조건을 확인한 FINAL 생성

## 빠른 시작

Linux / WSL의 **저장소 루트** (`group_3/`)에서 실행합니다. 원본 사진·라벨은 `subject7/data/raw/`에 별도로 준비합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r subject7/requirements.txt
cd subject7
../.venv/bin/python main.py
```

Windows 실행·Tkinter 설치·기존 검수 작업 복원은 [상세 가이드](docs/project/guides/labeling.md)에 있습니다.

## 검수 결과

| 전수 교차검수 | 라벨 변경 | 최종 QA |
|:---:|:---:|:---:|
| **900 / 900장** | **235장** | **FAIL 0 · REVIEW 0** |

최종 BBox는 4,561개이며, 실제 데이터 900장의 저장·재로드 비교도 일치했습니다.

[QA 결과](reports/qa_summary.md) · [테스트 결과](reports/test_report.md) · [최종본 증빙](reports/final_evidence.md)

## 문서 안내

| 필요한 내용 | 문서 |
|---|---|
| 설치·조작·최종본 생성 | [상세 사용 가이드](docs/project/guides/labeling.md) |
| Class·BBox·검수표 기준 | [프로젝트 문서](docs/project/README.md) |
| 파일별 설명·테스트 실행 | [코드 문서 목차](docs/README.md) |
| 모델 학습으로 이어가기 | [교과 8 인계](docs/project/handoff/subject08_handoff.md) |

<details>
<summary>폴더 구조와 알아둘 점</summary>

```text
subject7/
├── main.py                 프로그램 시작
├── configs/                Class 설정
├── src/ · tools/ · tests/  코드·처리 도구·테스트
├── docs/                   미러 설명서 + project/ 상세 문서
├── data/ · manifests/     RAW·WORK·FINAL·검수표
└── reports/                QA·테스트·최종본 증빙
```

- RAW는 수정하지 않고 WORK에 저장합니다. `수정 필요` 사진은 재검수하며 최종본에 바로 포함하지 않습니다.
- 원본 사진·RAW·WORK·작업 중 검수표는 Git에서 제외됩니다. 최종 라벨·`data/final/검수표.csv`·`classes.txt`는 원본 사진과 함께 [복원 도구](docs/tools/restore_from_final.md)로 복원할 수 있습니다.
- 검수 상태의 `수정 완료` 장수와 실제 라벨 변경 장수는 다릅니다. 차이 9장의 설명은 QA 보고서에 있습니다.
- 정상 김치 사진은 0장입니다. 검수표 일부 확인 칸은 상태 기록으로 갈음했으며, 자동 시험·사람 확인의 근거는 테스트 보고서에 구분했습니다.
- WSL 한글 입력·폴더 끌어다 놓기 등 환경 제약은 [상세 가이드의 제한사항](docs/project/guides/labeling.md#16-알려진-제한사항)을 봅니다.

</details>
