# 문서 목차

문서는 일차별이 아니라 **주제별 폴더**로 정리합니다. 같은 기준을 여러 곳에 따로 쓰지 않고, 기준은 `standards/` 한 곳에서만 고칩니다.

| 폴더 | 무엇이 있나 | 문서 |
|---|---|---|
| **standards/** 기준서 | 팀이 지키는 기준. **여기만 고치면 됩니다** | [project_baseline](standards/project_baseline.md) 팀 운영 기준 · [class_guide](standards/class_guide.md) Class 기준 · [bbox_guide](standards/bbox_guide.md) BBox 기준 · [manifest_guide](standards/manifest_guide.md) 검수표 작성 |
| **design/** 설계 | 만들 프로그램의 기능·화면·동작 | [필수기능목록](design/필수기능목록.md) · [기능목록_화면설계](design/기능목록_화면설계.md) · [의사코드](design/의사코드.md) · [EndToEnd_실행계획](design/EndToEnd_실행계획.md) · [Manifest_초안_참고용](design/Manifest_초안_참고용.md) |
| **survey/** 데이터 조사 | 데이터 구조와 사진 살펴보기 | [데이터조사표](survey/데이터조사표.md) |
| **team/** 팀 운영 | 역할 분담, Daily Gate 확인, 팀원 라벨 합치기 | [역할분담_DailyGate](team/역할분담_DailyGate.md) · [Gate_체크리스트](team/Gate_체크리스트.md) · [라벨_합치기](team/라벨_합치기.md) · [결과_주고받기](team/결과_주고받기.md) · [검수_배정](team/검수_배정.md) |
| **handoff/** 인계 | 교과 8 로 넘기는 최종 데이터 설명 | [subject08_handoff](handoff/subject08_handoff.md) |
| **records/** 작업 기록 | 과정 기록, 산출물 요약 | [과정기록](records/과정기록.md) · [산출물_요약](records/산출물_요약.md) · [이슈기록](records/이슈기록.md) |
| **meetings/** 회의록 | 일차별 회의록 | [1일차](meetings/회의록_1일차.md) · [2일차](meetings/회의록_2일차.md) · [3일차](meetings/회의록_3일차.md) |
| **images/** | 문서에 쓰는 그림 | |

시험 결과는 [reports/test_report.md](../reports/test_report.md), 품질검사 결과는 [reports/qa_summary.md](../reports/qa_summary.md), 검수표는 `manifests/` 에 있습니다.

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
