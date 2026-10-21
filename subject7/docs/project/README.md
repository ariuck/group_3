# 교과 7 · 프로젝트 문서

[← 문서 목차](../README.md) · [교과 7 README](../../README.md)

코드 한 파일의 설명서는 `docs/src/`·`docs/tools/`·`docs/tests/`에 있습니다. 이 폴더는 여러 코드에 걸친 사용법·기준·설계·운영 기록을 모읍니다. QA·테스트 결과의 근거는 [`reports/`](../../reports/)에 있습니다.

| 분류 | 읽을 문서 |
|---|---|
| **설치·사용** | [라벨링 도구 상세 가이드](guides/labeling.md) — 설치·조작·YOLO 형식·최종본 생성 |
| **기준서** | [팀 운영 기준](standards/project_baseline.md) · [Class](standards/class_guide.md) · [BBox](standards/bbox_guide.md) · [검수표](standards/manifest_guide.md) |
| **설계** | [필수 기능](design/필수기능목록.md) · [기능·화면 설계](design/기능목록_화면설계.md) · [의사코드](design/의사코드.md) · [실행 계획](design/EndToEnd_실행계획.md) · [검수표 초안](design/Manifest_초안_참고용.md) |
| **팀 운영** | [역할·Daily Gate](team/역할분담_DailyGate.md) · [체크리스트](team/Gate_체크리스트.md) · [검수 배정](team/검수_배정.md) · [라벨 합치기](team/라벨_합치기.md) · [결과 공유](team/결과_주고받기.md) |
| **데이터 조사** | [데이터 조사표](survey/데이터조사표.md) |
| **작업 기록** | [과정 기록](records/과정기록.md) · [산출물 요약](records/산출물_요약.md) · [이슈](records/이슈기록.md) · [발표 요약 원본](records/PROJECT7_INFOGRAPHIC_SOURCE.md) |
| **회의록** | [1일차](meetings/회의록_1일차.md) · [2일차](meetings/회의록_2일차.md) · [3일차](meetings/회의록_3일차.md) |
| **인계** | [교과 7 → 교과 8](handoff/subject08_handoff.md) |

설계·회의록은 당시의 계획과 결정 과정을 보존합니다. 실제 검수 작업에는 `standards/`의 확정 기준을, 수치에는 QA·테스트 보고서를 우선합니다.

## 초안과 최종 기준이 다른 부분 (최종 기준이 우선)

초기에 쓴 설계 초안 중 **팀이 확정한 검수표**와 이름·값이 다른 것이 있습니다. 아래는 검수표를 따릅니다.

| 항목 | 초기 초안 | 최종 (검수표) |
|---|---|---|
| Manifest 파일 | `manifests/manifest.csv` (14칸) | `manifests/dataset_manifest.xlsx` — 시트 `검수표` 19칸 + `Class 기준`, CSV 는 `dataset_manifest.csv` |
| 작업 상태 | PENDING / WORKING / PASS / EDITED / REVIEW / REVIEWED / FINAL | `상태` = 검수 전 / 검수 완료 / 수정 필요 / 수정 완료 / 제외 |
| 검수 사유 | 자유 문장(`issue`) | `발견된 문제`, `비고(수정 내용)` 칸 |
| Class 설정 | `config/classes.json` | `configs/classes.yaml` |
| 기준 문서 | 산출물 안의 기준 정리 | [standards/](standards/) 의 기준서 |

[Manifest 초안](design/Manifest_초안_참고용.md)은 칸의 **뜻을 이해하기 위한 참고**로만 보고, 실제 작업 기록은 검수표(`dataset_manifest.xlsx`) 틀로 합니다.

### 검수표 틀에 더한 것 (팀 결정 반영)

- **출처 데이터셋 / 원래 split 칸을 맨 끝(R, S열)에 추가했습니다.** 교과 8 에서 출처와 기존 분할을 확인하기 위한 것이며, 선택 목록(`이물검출_학습데이터1·2`, `train·validation`)이 붙어 있습니다.
- **REVIEW 는 `상태 = 수정 필요` + `발견된 문제 = REVIEW: 이유 코드` 로 표시합니다.** 상태 목록은 그대로 두었습니다.
- 자세한 작성 방법: [manifest_guide](standards/manifest_guide.md)

## 알아 둘 점

- 문서의 예시 이미지·BBox 는 설명용으로 만든 **가상 샘플**입니다. (회사 데이터가 아님)
- 문서의 `【기입】`, `【내 칸】` 은 팀이 직접 확인해서 채우는 칸입니다.


[코드 문서화 중 남긴 확인 항목](records/code_review_notes.md)은 현재 구현과 다시 대조할 참고 목록입니다.
