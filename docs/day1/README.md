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

1일차에 쓴 초안 중 **최종 제출 기준과 이름·값이 다른 것**이 있습니다. 아래는 최종 기준을 따릅니다.

| 항목 | 1일차 초안 | 최종 기준 |
|---|---|---|
| Manifest 파일 | `manifests/manifest.csv` (14칸) | `manifests/dataset_manifest.csv` (8칸: `file_name, source_dataset, original_split, scene_type, worker, status, qa_status, review_reason`) |
| 작업 상태 | PENDING / WORKING / PASS / EDITED / REVIEW / REVIEWED / FINAL | `status` = DONE / EDITED / REVIEW, `qa_status` = PASS / WAIT |
| 검수 사유 | 자유 문장(`issue`) | `review_reason` 코드 (예: `class_ambiguous`, `bbox_boundary_ambiguous`) |
| Class 설정 | `config/classes.json` | `configs/classes.yaml` |
| 기준 문서 | 1일차_산출물 안의 기준 정리 | `docs/project_baseline.md`, `class_guide.md`, `bbox_guide.md` |

1일차 문서의 Manifest 초안(`3_Dataset_Manifest_초안`)은 칸의 **뜻을 이해하기 위한 참고**로만 보고,
실제 작업 기록은 `dataset_manifest.csv` 형식으로 합니다.

## 알아 둘 점

- 문서의 예시 이미지·BBox 는 설명용으로 만든 **가상 샘플**입니다. (회사 데이터가 아님)
- 문서의 `【기입】`, `【내 칸】` 은 팀이 직접 확인해서 채우는 칸입니다.
