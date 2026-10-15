# 코드 문서 목차 (코드 파일 1개 = 문서 1개)

코드 경로를 그대로 따라 만든다. `src/ui/tooltip.py` → [`docs/code/src/ui/tooltip.md`](src/ui/tooltip.md)

- 이 폴더는 **파일 하나하나의 설명서**(입출력, 함수, 의존 관계, 주의사항)다.
- 전체 기준·설계·팀 운영 같은 "숲"을 보는 문서는 [문서 목차](../README.md)의 주제별 폴더(standards, design, team …)에 그대로 있다.
- 내용이 없는 `__init__.py` 는 문서를 만들지 않는다.

[README §3 폴더 구조](../../README.md) 와 함께 보면 좋다.

## 모듈 관계

```D:\ai_이유정강사님_수업\Vision_AI_Class-main\handgonpo Vision_AI_Class main 교과 8 프로젝트 1\1. 교과8_Vision_객체검출_프로젝트_수행가이드.md
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
         check_docs                                                       ← 이 문서 폴더 점검

subject8_kimchi_detection/   교과 8 (자체 src/ 를 가진 별도 프로젝트)
```

## `main.py` · `src/`

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

## `tools/`

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

## `tests/`

전체 실행: [`run_all.py`](tests/run_all.md) (`python tests/run_all.py`, 약 1분)

| 화면 없이 | 화면(Tk) 필요 |
|---|---|
| [`test_bbox_diff`](tests/test_bbox_diff.md) · [`test_bbox_edit`](tests/test_bbox_edit.md) · [`test_viewport`](tests/test_viewport.md) · [`test_data_paths`](tests/test_data_paths.md) · [`test_validator`](tests/test_validator.md) · [`test_navigator`](tests/test_navigator.md) · [`test_folder_drop`](tests/test_folder_drop.md) · [`test_manifest_input`](tests/test_manifest_input.md) | [`day1_selftest`](tests/day1_selftest.md) · [`test_edit_ui`](tests/test_edit_ui.md) · [`test_quick_review`](tests/test_quick_review.md) · [`test_step_hold`](tests/test_step_hold.md) · [`test_filter_ui`](tests/test_filter_ui.md) · [`test_form_panel`](tests/test_form_panel.md) · [`test_hangul_input`](tests/test_hangul_input.md) · [`test_theme`](tests/test_theme.md) · [`test_thumb_strip`](tests/test_thumb_strip.md) · [`test_tooltip_help`](tests/test_tooltip_help.md) |
| 도구: [`test_build_final`](tests/test_build_final.md) · [`test_export_manifest_xlsx`](tests/test_export_manifest_xlsx.md) · [`test_final_evidence`](tests/test_final_evidence.md) · [`test_import_labels`](tests/test_import_labels.md) · [`test_merge_manifests`](tests/test_merge_manifests.md) · [`test_pack_results`](tests/test_pack_results.md) · [`test_qa_summary`](tests/test_qa_summary.md) · [`test_share_server`](tests/test_share_server.md) | 일부 화면: [`test_box_problems`](tests/test_box_problems.md) · [`test_label_io`](tests/test_label_io.md) · [`test_manifest_edge`](tests/test_manifest_edge.md) · [`test_session`](tests/test_session.md) |

## `subject8_kimchi_detection/` (교과 8)

| 코드 | 한 줄 설명 |
|---|---|
| [`scripts/01_check_environment.py`](subject8_kimchi_detection/scripts/01_check_environment.md) | PyTorch·CUDA·YOLO11n 환경 점검 |
| [`scripts/02_audit_subject7_final.py`](subject8_kimchi_detection/scripts/02_audit_subject7_final.md) | 교과 7 최종본 900장 점검 + Data Leakage 확인 |
| [`scripts/03_build_split.py`](subject8_kimchi_detection/scripts/03_build_split.md) | 방안 B 분할 + Manifest·`dataset.yaml` |
| [`scripts/04_import_label_fixes.py`](subject8_kimchi_detection/scripts/04_import_label_fixes.md) | 라벨링 프로그램 수정본 → `kimchi_v3` 라벨 수정본 + 변경 기록 |
| [`scripts/05_smoke_train.py`](subject8_kimchi_detection/scripts/05_smoke_train.md) | Smoke Test (Train 40 / Val 8, 3 epoch → Prediction) |
| [`scripts/06_train_baseline.py`](subject8_kimchi_detection/scripts/06_train_baseline.md) | 공식 Baseline 학습 (`kimchi_v4` · YOLO11n · 640) + Weight 보관 + 학습 조건 기록 |
| [`scripts/07_evaluate_baseline.py`](subject8_kimchi_detection/scripts/07_evaluate_baseline.md) | Baseline Validation 평가 → `baseline_metrics.csv`·Class 별 성능·그래프 |
| [`scripts/08_predict_images.py`](subject8_kimchi_detection/scripts/08_predict_images.md) | 사진 예측 + 정답 비교 이미지 · TP/FP/FN 표 |
| [`scripts/plot_runs.py`](subject8_kimchi_detection/scripts/plot_runs.md) | 모든 실행의 학습 곡선 · Version 별 비교 그래프 · `runs_summary.csv` (results.csv 만으로) |
| [`scripts/09_collect_failures.py`](subject8_kimchi_detection/scripts/09_collect_failures.md) | 실패 사례 수집 → `failure_analysis.csv` · 요약 표 · 대표 사진 |
| [`scripts/10_train_v2.py`](subject8_kimchi_detection/scripts/10_train_v2.md) | 개선 실험 exp001 — Baseline 조건에서 imgsz 640 → 1280 (공식: `kimchi_v4`) |
| [`src/constants.py`](subject8_kimchi_detection/src/constants.md) | Class·장면·묶음 기준·Version 별 분할 규칙·역할 상수 (SSOT) |
| [`src/dataset_audit.py`](subject8_kimchi_detection/src/dataset_audit.md) | `DatasetAuditor` — 라벨 점검, 이미지별 BBox 수, Class×장면 |
| [`src/evaluate_detector.py`](subject8_kimchi_detection/src/evaluate_detector.md) | Weight 평가 (전체·Class 별 P·R·mAP), Frozen Test 보호 |
| [`src/failure_analyzer.py`](subject8_kimchi_detection/src/failure_analyzer.md) | 실패 유형 분류(FN·CLASS_ERROR·FP 3종) · 크기별 Recall · Train/Val 비교 사진 |
| [`src/inference.py`](subject8_kimchi_detection/src/inference.md) | 예측 ↔ 정답 짝짓기 (TP·CLASS_ERROR·FP·FN), 비교 이미지 |
| [`src/leakage_check.py`](subject8_kimchi_detection/src/leakage_check.md) | 사진 지문(dHash)으로 촬영 묶음 누수 확인 |
| [`src/smoke_dataset.py`](subject8_kimchi_detection/src/smoke_dataset.md) | Smoke Test 용 작은 Dataset 만들기 |
| [`src/split_builder.py`](subject8_kimchi_detection/src/split_builder.md) | `SplitBuilder` — 촬영 묶음 단위 분할 |
| [`src/train_detector.py`](subject8_kimchi_detection/src/train_detector.md) | YOLO 학습 공통 함수 · 학습 점검 · 조건 기록 |
## 문서 작성 규칙

1. 코드 파일을 **추가·이름 변경·삭제**하면 같은 커밋에서 이 폴더의 문서도 함께 추가·이동·삭제한다.
2. 문서 순서: 한 줄 요약 → 역할 → 주요 구성요소(표) → 의존성(사용하는 것 / 사용하는 곳) → 사용 예·핵심 동작 → 주의사항. 테스트 문서는 실행 방법과 시험 내용만 짧게 쓴다.
3. 커밋 전에 대응 여부를 점검한다.

   ```bash
   python tools/check_docs.py
   ```

## 문서를 쓰며 발견한 점

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