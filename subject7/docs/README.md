# 문서 목차 (교과 7)

```
docs/
├─ src/ · tools/ · tests/ · main.md   코드 설명서 — 코드와 같은 경로 (src/ui/tooltip.py → docs/src/ui/tooltip.md)
└─ project/                           그 밖의 프로젝트 문서 전부 (기준서·설계·팀 운영·기록·회의록·그림)
```

- **코드 파일이 궁금하면** 코드 경로 앞에 `docs/` 를 붙인다 → [아래 코드 문서 목차](#코드-문서-코드-파일-1개--문서-1개)
- **그 밖의 것은 `project/` 안**에 주제별 폴더로 있다. 일차별이 아니라 주제별로 정리하고, 기준은 `project/standards/` 한 곳에서만 고친다.

## `project/` — 프로젝트 문서

| 폴더 | 무엇이 있나 | 문서 |
|---|---|---|
| **standards/** 기준서 | 팀이 지키는 기준. **여기만 고치면 됩니다** | [project_baseline](project/standards/project_baseline.md) 팀 운영 기준 · [class_guide](project/standards/class_guide.md) Class 기준 · [bbox_guide](project/standards/bbox_guide.md) BBox 기준 · [manifest_guide](project/standards/manifest_guide.md) 검수표 작성 |
| **design/** 설계 | 만들 프로그램의 기능·화면·동작 | [필수기능목록](project/design/필수기능목록.md) · [기능목록_화면설계](project/design/기능목록_화면설계.md) · [의사코드](project/design/의사코드.md) · [EndToEnd_실행계획](project/design/EndToEnd_실행계획.md) · [Manifest_초안_참고용](project/design/Manifest_초안_참고용.md) |
| **survey/** 데이터 조사 | 데이터 구조와 사진 살펴보기 | [데이터조사표](project/survey/데이터조사표.md) |
| **team/** 팀 운영 | 역할 분담, Daily Gate 확인, 팀원 라벨 합치기 | [역할분담_DailyGate](project/team/역할분담_DailyGate.md) · [Gate_체크리스트](project/team/Gate_체크리스트.md) · [라벨_합치기](project/team/라벨_합치기.md) · [결과_주고받기](project/team/결과_주고받기.md) · [검수_배정](project/team/검수_배정.md) |
| **handoff/** 인계 | 교과 8 로 넘기는 최종 데이터 설명 | [subject08_handoff](project/handoff/subject08_handoff.md) |
| **records/** 작업 기록 | 과정 기록, 산출물 요약 | [과정기록](project/records/과정기록.md) · [산출물_요약](project/records/산출물_요약.md) · [이슈기록](project/records/이슈기록.md) · [PROJECT7_INFOGRAPHIC_SOURCE](project/records/PROJECT7_INFOGRAPHIC_SOURCE.md) 발표·인포그래픽용 요약 |
| **meetings/** 회의록 | 일차별 회의록 | [1일차](project/meetings/회의록_1일차.md) · [2일차](project/meetings/회의록_2일차.md) · [3일차](project/meetings/회의록_3일차.md) |
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
| 기준 문서 | 산출물 안의 기준 정리 | [standards/](project/standards/) 의 기준서 |

[Manifest 초안](project/design/Manifest_초안_참고용.md)은 칸의 **뜻을 이해하기 위한 참고**로만 보고, 실제 작업 기록은 검수표(`dataset_manifest.xlsx`) 틀로 합니다.

### 검수표 틀에 더한 것 (팀 결정 반영)

- **출처 데이터셋 / 원래 split 칸을 맨 끝(R, S열)에 추가했습니다.** 교과 8 에서 출처와 기존 분할을 확인하기 위한 것이며, 선택 목록(`이물검출_학습데이터1·2`, `train·validation`)이 붙어 있습니다.
- **REVIEW 는 `상태 = 수정 필요` + `발견된 문제 = REVIEW: 이유 코드` 로 표시합니다.** 상태 목록은 그대로 두었습니다.
- 자세한 작성 방법: [manifest_guide](project/standards/manifest_guide.md)

## 알아 둘 점

- 문서의 예시 이미지·BBox 는 설명용으로 만든 **가상 샘플**입니다. (회사 데이터가 아님)
- 문서의 `【기입】`, `【내 칸】` 은 팀이 직접 확인해서 채우는 칸입니다.

## 코드 문서 (코드 파일 1개 = 문서 1개)

코드 경로 앞에 `docs/` 만 붙이면 그 파일의 설명서가 나온다. `src/ui/tooltip.py` → [`docs/src/ui/tooltip.md`](src/ui/tooltip.md)

- 파일 하나하나의 설명서(입출력, 함수, 의존 관계, 주의사항)다. 전체 기준·설계·팀 운영은 위 `project/` 를 본다.
- 내용이 없는 `__init__.py` 는 문서를 만들지 않는다.

### 모듈 관계

```
main.py
  └─ src/ui/main_window.py ─────────────────────────────── 화면·이벤트·흐름
       ├─ src/ui/ form_panel(+hangul_input) · thumb_strip · navigator · class_picker
       │          · session · folder_drop · tooltip · help_dialog · validation_dialog · theme
       ├─ src/bbox/ bbox_manager · bbox_edit · bbox_diff · history · viewport   ← 화면 없는 계산
       ├─ src/yolo/ coords · yolo_loader · yolo_writer                           ← TXT 읽기·쓰기
       ├─ src/manifest/manifest_writer.py                                        ← 검수표 CSV
       ├─ src/validation/validator.py                                            ← 데이터 조사·QA
       └─ src/data_paths.py ── src/settings.py ── configs/classes.yaml           ← 경로·Class

tools/   import_labels · pack_results · merge_manifests · share_server   ← 팀원끼리 결과 주고받기
         build_final · export_manifest_xlsx · final_evidence · qa_summary ← 최종본·보고서
         check_docs                                                       ← 코드 ↔ 문서 대응 점검

(교과 8 은 저장소의 subject8/ — 코드 문서도 같은 규칙으로 subject8/docs/ 에 있다)
```

### `main.py` · `src/`

| 코드 | 한 줄 설명 |
|---|---|
| [`main.py`](main.md) | 프로그램 시작 |
| [`src/settings.py`](src/settings.md) | 경로(RAW/WORK/FINAL/검수표)와 `classes.yaml` Class 기준 |
| [`src/data_paths.py`](src/data_paths.md) | RAW 와 같은 구조의 WORK 경로, RAW 보호, `Zone.Identifier` 정리 |
| [`src/yolo/coords.py`](src/yolo/coords.md) | YOLO 비율 ↔ 픽셀 좌표 |
| [`src/yolo/yolo_loader.py`](src/yolo/yolo_loader.md) | 원본 TXT 찾기·읽기, 내용 비교 서명 |
| [`src/yolo/yolo_writer.py`](src/yolo/yolo_writer.md) | YOLO TXT 저장 |
| [`src/bbox/bbox_manager.py`](src/bbox/bbox_manager.md) | BBox 만들기·선택·이상 검사 |
| [`src/bbox/bbox_edit.py`](src/bbox/bbox_edit.md) | 이동·8방향 크기 조절 |
| [`src/bbox/bbox_diff.py`](src/bbox/bbox_diff.md) | RAW ↔ 지금: 그대로·수정·추가·삭제 |
| [`src/bbox/history.py`](src/bbox/history.md) | Undo / Redo |
| [`src/bbox/viewport.py`](src/bbox/viewport.md) | 확대·이동 좌표 계산 |
| [`src/manifest/manifest_writer.py`](src/manifest/manifest_writer.md) | 검수표 CSV 기록, **상태 자동 결정 규칙** |
| [`src/validation/validator.py`](src/validation/validator.md) | 데이터 조사 + QA 검증 코드 12종 |

### `src/ui/`

| 코드 | 한 줄 설명 |
|---|---|
| [`main_window.py`](src/ui/main_window.md) | 메인 화면. 저장 흐름, 한 키 검수, 비동기 사진 이동 |
| [`form_panel.py`](src/ui/form_panel.md) | 검수 기록 입력칸 (상태·이미지 유형·작성자·검수자 …) |
| [`hangul_input.py`](src/ui/hangul_input.md) | WSL 용 두벌식 한글 조합기 |
| [`thumb_strip.py`](src/ui/thumb_strip.md) | 하단 썸네일 줄 |
| [`navigator.py`](src/ui/navigator.md) | 사진 목록·이전/다음·필터 |
| [`session.py`](src/ui/session.md) | 마지막 작업 위치 기억 |
| [`theme.py`](src/ui/theme.md) | 색·글꼴·위젯 스타일 |
| [`class_picker.py`](src/ui/class_picker.md) | Class 선택 목록 |
| [`folder_drop.py`](src/ui/folder_drop.md) | 폴더 끌어다 놓기 |
| [`help_dialog.py`](src/ui/help_dialog.md) | 단축키 도움말 (F1) |
| [`tooltip.py`](src/ui/tooltip.md) | 말풍선 |
| [`validation_dialog.py`](src/ui/validation_dialog.md) | QA 검증 결과 창 |

### `tools/`

| 코드 | 한 줄 설명 |
|---|---|
| [`import_labels.py`](tools/import_labels.md) | 받은 라벨을 `data/work` 로 가져오기 |
| [`pack_results.py`](tools/pack_results.md) | 내 결과(라벨+검수표)를 zip 으로, 번호 범위 지정 가능 |
| [`merge_manifests.py`](tools/merge_manifests.md) | 팀원 검수표 합치기 |
| [`share_server.py`](tools/share_server.md) | 같은 네트워크 임시 공유 서버 + 단계별 가이드 화면 |
| [`build_final.py`](tools/build_final.md) | 검수 완료본을 `data/final` 로 |
| [`export_manifest_xlsx.py`](tools/export_manifest_xlsx.md) | 검수표 CSV → 제출용 xlsx |
| [`final_evidence.py`](tools/final_evidence.md) | 최종본 증빙 숫자 |
| [`qa_summary.py`](tools/qa_summary.md) | `reports/qa_summary.md` 만들기 |
| [`check_docs.py`](tools/check_docs.md) | 이 폴더의 코드 ↔ 문서 대응 점검 |

### `tests/`

전체 실행: [`run_all.py`](tests/run_all.md) (`python tests/run_all.py`, 약 1분)

| 화면 없이 | 화면(Tk) 필요 |
|---|---|
| [`test_bbox_diff`](tests/test_bbox_diff.md) · [`test_bbox_edit`](tests/test_bbox_edit.md) · [`test_viewport`](tests/test_viewport.md) · [`test_data_paths`](tests/test_data_paths.md) · [`test_validator`](tests/test_validator.md) · [`test_navigator`](tests/test_navigator.md) · [`test_folder_drop`](tests/test_folder_drop.md) · [`test_manifest_input`](tests/test_manifest_input.md) | [`day1_selftest`](tests/day1_selftest.md) · [`test_edit_ui`](tests/test_edit_ui.md) · [`test_quick_review`](tests/test_quick_review.md) · [`test_step_hold`](tests/test_step_hold.md) · [`test_filter_ui`](tests/test_filter_ui.md) · [`test_form_panel`](tests/test_form_panel.md) · [`test_hangul_input`](tests/test_hangul_input.md) · [`test_theme`](tests/test_theme.md) · [`test_thumb_strip`](tests/test_thumb_strip.md) · [`test_tooltip_help`](tests/test_tooltip_help.md) |
| 도구: [`test_build_final`](tests/test_build_final.md) · [`test_export_manifest_xlsx`](tests/test_export_manifest_xlsx.md) · [`test_final_evidence`](tests/test_final_evidence.md) · [`test_import_labels`](tests/test_import_labels.md) · [`test_merge_manifests`](tests/test_merge_manifests.md) · [`test_pack_results`](tests/test_pack_results.md) · [`test_qa_summary`](tests/test_qa_summary.md) · [`test_share_server`](tests/test_share_server.md) | 일부 화면: [`test_box_problems`](tests/test_box_problems.md) · [`test_label_io`](tests/test_label_io.md) · [`test_manifest_edge`](tests/test_manifest_edge.md) · [`test_session`](tests/test_session.md) |

### 문서 작성 규칙

1. 코드 파일을 **추가·이름 변경·삭제**하면 같은 커밋에서 이 폴더의 문서도 함께 추가·이동·삭제한다.
2. 문서 순서: 한 줄 요약 → 역할 → 주요 구성요소(표) → 의존성(사용하는 것 / 사용하는 곳) → 사용 예·핵심 동작 → 주의사항. 테스트 문서는 실행 방법과 시험 내용만 짧게 쓴다.
3. 커밋 전에 대응 여부를 점검한다.

   ```bash
   python tools/check_docs.py
   ```

### 문서를 쓰며 발견한 점

코드를 바꾸지 않고 각 문서의 "주의사항"에 적어 둔 것 중 확인이 필요한 것들이다.

| 위치 | 내용 |
|---|---|
| [`main_window`](src/ui/main_window.md) | 검수 기록 칸만 고친 뒤 Undo/Redo 로 BBox 를 처음 상태로 돌리면 `dirty` 가 꺼져, 다음 사진으로 넘어갈 때 입력칸 변경이 묻지 않고 버려질 수 있다 |
| [`yolo_loader`](src/yolo/yolo_loader.md) ↔ [`validator`](src/validation/validator.md) | Class `2.0` 을 화면은 Class 2 로 읽고, Validation·`import_labels` 는 `BAD_NUMBER` 로 본다 |
| [`build_final`](tools/build_final.md) | `제외` 사진이 한 장이라도 있으면 최종본을 만들지 않는다 (건너뛰는 것이 아님) |
| [`import_labels`](tools/import_labels.md) | 덮어쓰기 백업이 원래 폴더 구조가 아니라 파일 이름만으로 저장된다 (docstring 과 다름) |
| [`share_server`](tools/share_server.md) | 기본 검수 범위에 501~550번이 빠져 있다. PM 가이드가 안내하는 `공유시작.bat` 은 저장소에 없다 |
| [`qa_summary`](tools/qa_summary.md) | 사람 이름·Human QA 결과·일부 수치 문장이 코드에 고정되어 있다 |
| [`yolo_writer`](src/yolo/yolo_writer.md) | TXT 를 원자적으로 저장하지 않는다 (검수표·세션은 원자적 저장) |
