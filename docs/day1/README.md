# 1일차 문서 모음

교과 7 1일차(데이터 이해 · 기준선 · 설계 · 첫 End-to-End)에 작성한 초안과 기록입니다.

| 문서 | 내용 |
|---|---|
| [1일차_체크리스트](1일차_체크리스트.md) | Daily Gate 10개 항목의 확인 방법과 상태, 데이터 조사 결과 |
| [day1_Must_Have_기능목록](day1_Must_Have_기능목록.md) | Must Have 기능 목록 (M01~M25) |
| [day1_의사코드](day1_의사코드.md) | 1일차 프로그램의 동작 순서 |
| [day1_간단기록/1일차_산출물](day1_간단기록/1일차_산출물.md) | 1일차 산출물 5개 |
| [day1_간단기록/1일차_과정기록](day1_간단기록/1일차_과정기록.md) | 6단계 과정 기록 |

## 최종 기준과 다른 부분 (최종 기준이 우선)

1일차에 쓴 초안 중 **팀이 확정한 Manifest 검수표**와 이름·값이 다른 것이 있습니다. 아래는 검수표를 따릅니다.

| 항목 | 1일차 초안 | 최종 (검수표) |
|---|---|---|
| Manifest 파일 | `manifests/manifest.csv` (14칸) | `manifests/dataset_manifest.xlsx` — 시트 `검수표` 17칸 + `Class 기준`, CSV 머리글은 `dataset_manifest.csv` |
| 작업 상태 | PENDING / WORKING / PASS / EDITED / REVIEW / REVIEWED / FINAL | `상태` = 검수 전 / 검수 완료 / 수정 필요 / 수정 완료 / 제외 |
| 검수 사유 | 자유 문장(`issue`) | `발견된 문제`, `비고(수정 내용)` 칸 |
| Class 설정 | `config/classes.json` | `configs/classes.yaml` |
| 기준 문서 | 1일차_산출물 안의 기준 정리 | `docs/project_baseline.md`, `class_guide.md`, `bbox_guide.md` |

1일차 문서의 Manifest 초안(`3_Dataset_Manifest_초안`)은 칸의 **뜻을 이해하기 위한 참고**로만 보고,
실제 작업 기록은 검수표(`dataset_manifest.xlsx`) 틀로 합니다.

### 검수표 틀에 아직 없는 것 (팀 결정 필요)

- **출처(`source_dataset`)·원래 split(`train`/`validation`) 칸이 없습니다.** 교과 8 에서 출처와 기존 분할을 확인해야 하므로 칸을 추가할지 정해야 합니다.
- **REVIEW(판단이 어려움)에 해당하는 상태가 없습니다.** Class/BBox 기준서의 "애매하면 REVIEW"를 검수표에서 어떻게 표시할지 정해야 합니다. (예: 상태 `수정 필요` + `발견된 문제`에 이유)

## 알아 둘 점

- 문서의 예시 이미지·BBox 는 설명용으로 만든 **가상 샘플**입니다. (회사 데이터가 아님)
- 문서의 `【기입】`, `【내 칸】` 은 팀이 직접 확인해서 채우는 칸입니다.
