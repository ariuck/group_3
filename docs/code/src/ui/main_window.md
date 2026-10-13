# `src/ui/main_window.py`

> 라벨링 프로그램의 **메인 화면** (Tkinter). 사진 열기 → 기존 TXT 로드 → BBox 편집 → WORK 저장 + 검수표 기록 → 다음 사진까지 전 과정을 묶는다. 계산은 `src/bbox`, `src/yolo`, `src/manifest` 등에 맡기고 이 파일은 화면·이벤트·흐름을 담당한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/ui/main_window.py)

## 역할

- 핵심 약속: BBox 는 **원본 이미지 픽셀 좌표**로 기억하고, 그릴 때만 [`Viewport`](../bbox/viewport.md) 로 화면 좌표로 바꾼다.
- RAW 는 절대 수정하지 않는다. 저장 경로가 RAW 안이면 저장을 거부한다.
- 900장을 빠르게 넘기며 검수하는 흐름(`Enter` / `R` / `N` / `W`)과, 방향키를 꾹 눌러도 멈추지 않는 비동기 사진 읽기를 제공한다.

실행: 루트에서 `python main.py` ([`main.py`](../../main.md))

## 화면 구성

```
┌ 도구 줄: [이미지 열기][폴더 열기] | [저장][저장+다음] | [↶][↷][삭제][전체 삭제] | [⤢][－][＋][이동 모드] | [도구 ▾]     배율% ┐
├──────────────────────────────────────────────────────────────────────────────┬──────────────────────┤
│ 보기: □RAW 와 비교(Diff) □BBox 보기 □십자선 | 밝기 대비 흑백   추가·수정·삭제 요약  │ 클래스 (ClassPicker)   │
│ 파일 이름  ● 저장 안 됨                                  ◀ 이전 [번호] / N 이동 다음 ▶ │                      │
│ 데이터셋 / split · W×H px                                                     │ 라벨 목록 (Treeview)   │
│ ⚠ 경고 줄 (읽지 못한 줄 · 확인 필요 BBox · 검수표 읽기 실패)                       │ No·클래스·위치·상태     │
│                                                                              │                      │
│                       Canvas (이미지 + BBox + 핸들)                            │                      │
│                                                                              ├──────────────────────┤
│ 좌표줄: BBox n번 · Class · x1,y1 x2,y2 · W×H · YOLO 값 · ⚠ 문제                   │ 검수 기록 (FormPanel)  │
│ 이미지 목록 (ThumbStrip)  작업 진행 요약                          보기 [필터 ▾]     │                      │
├──────────────────────────────────────────────────────────────────────────────┴──────────────────────┤
│ 상태줄 (결과 메시지는 5초 동안 마우스 좌표 안내가 덮지 못함)                                                      │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

`도구` 메뉴: 데이터 조사 · QA 검증 (무결성) · 다시 불러오기 · WORK 폴더 열기 · 단축키 도움말

## 주요 구성요소

클래스는 `Day1Labeler` 하나이며, 1일차 이름을 그대로 쓴다. 메서드를 기능별로 묶으면 아래와 같다.

| 묶음 | 메서드 | 설명 |
|---|---|---|
| 시작 | `__init__`, `start_message`, `build_widgets`, `bind_events`, `main()` | `theme.setup` → 위젯 → 단축키 → 150ms 뒤 `restore_session`. `main()` 은 시작 전 `Zone.Identifier` 정리 |
| 조사·검증 | `show_inventory`, `run_validation`, `open_work_folder` | [`scan_inventory`](../validation/validator.md) 결과를 Markdown 으로 보여 주고 복사. 검증 결과는 `reports/validation_report.csv` 저장 후 [`ValidationDialog`](validation_dialog.md), 더블클릭 → [`find_raw_image`](../data_paths.md) → `move_to` |
| 열기 | `open_image`, `open_folder`, `open_folder_path`, `on_drop`, `restore_session`, `on_window_focus` | 폴더는 [`ImageNavigator.load_folder`](navigator.md). RAW 밖 폴더면 "검수표에 기록되지 않음" 안내 |
| 사진 올리기 | `decode_image`, `load_image`, `apply_image`, `load_boxes`, `load_form` | 라벨 우선순위: **WORK → RAW → 없음**. RAW 는 Diff 비교용으로 따로 읽어 `raw_boxes` 에 둔다 |
| 사진 이동 | `step`, `flush_step`, `start_async_load`, `poll_load`, `go_prev/next`, `move_to`, `jump_to_entered_index`, `go_next_unworked`, `update_nav`, `wait_for_nav` | 아래 "비동기 사진 이동" 참고 |
| 저장 | `save`, `save_and_next`, `confirm_discard`, `reload` | 아래 "저장 흐름" 참고 |
| 한 키 검수 | `mark_ok_and_next` (Enter), `mark_review` (R), `on_form_submit`, `check_scene_type`, `choose_scene` | |
| 목록·필터 | `refresh_file_list`, `update_summary`, `status_map`, `make_filter`, `on_filter_changed`, `thumb_mark`, `on_thumb_selected` | 검수표는 **수정 시각이 바뀔 때만** 다시 읽는다 (`_status_cache`) |
| 그리기 | `show_image`, `render`, `draw_boxes`, `draw_ghost`, `enhance`, `update_cross`, `update_warning`, `update_bbox_info`, `refresh_box_list`, `update_title` | 이미지(`img` 태그)와 BBox(`box` 태그)를 따로 그린다 |
| 보기 옵션 | `cycle_brightness`, `cycle_contrast`, `on_gray_clicked`, `on_diff_toggled`, `on_cross_toggled`, `toggle_boxes` | 밝기·대비 단계 `1.0 → 1.3 → 1.6 → 0.7`. 화면에만 적용 |
| 확대·이동 | `zoom`, `zoom_in/out`, `fit_to_window`, `on_mouse_wheel`, `on_pan_start/drag/end`, `on_canvas_resize`, `on_resize_done` | Pan 중에는 그려진 것을 `canvas.move` 로 옮기고 40ms 뒤 다시 그림 |
| 마우스 편집 | `on_mouse_down/drag/up`, `start_edit`, `finish_edit`, `cancel_drag`, `on_escape`, `update_hover_cursor`, `on_mouse_move` | 아래 "마우스 판정 순서" 참고 |
| BBox 편집 | `select_box`, `select_next_box` (Tab), `nudge` (Shift+방향키), `delete_selected`, `clear_all`, `choose_class`, `mark_changed` | 모든 편집은 바꾸기 **직전**에 `history.push` |
| Undo | `undo`, `redo`, `after_history` | 처음 상태까지 되돌리면 `dirty = False` |
| 정리 | `shutdown`, `on_close` | 예약 작업·말풍선·썸네일 읽기 취소 후 창 닫기 |

## 핵심 동작

### 저장 흐름 (`save`)

1. 원본에 읽지 못한 줄이 있으면 "그 줄은 WORK 에서 빠진다"고 한 번 확인 (같은 사진은 다시 묻지 않음)
2. 저장 경로가 RAW 안이면 **저장 거부** ([`is_inside`](../data_paths.md))
3. [`write_yolo_file`](../yolo/yolo_writer.md) 로 WORK 에 TXT 저장
4. [`record_save`](../manifest/manifest_writer.md) 로 검수표 기록 (입력칸 값 함께). 실패하면 TXT 는 저장된 채 **`dirty` 를 유지**하고 경고
5. 입력칸을 검수표 값으로 다시 채움 (프로그램이 정한 상태를 보여 줌), 썸네일 ✓·요약 갱신

### 한 키 검수

| 키 | 동작 |
|---|---|
| `Enter` | 이미지 유형이 비어 있으면 그 칸을 깜빡이고 멈춤. 아니면 [`diff_boxes`](../bbox/bbox_diff.md) 로 원본과 비교해 상태를 **수정 완료 / 검수 완료** 로 정하고 저장 + 다음 |
| `R` | 상태 = 수정 필요, `발견된 문제` 가 비었으면 `REVIEW: ` 를 채우고 커서를 그 칸으로. 이유를 쓰고 `Enter` → 저장 + 다음 |
| `N` | 검수표에 기록이 없는 다음 사진으로 (끝까지 없으면 처음부터) |
| `W` | 상태는 그대로 두고 저장 + 다음 |

### 비동기 사진 이동 (`step` → `flush_step` → `start_async_load` → `poll_load`)

- 방향키를 누르는 동안에는 번호·썸네일 강조만 바로 바꾸고, 사진은 입력이 잠잠해질 때(`after_idle`) **마지막 목적지 한 장만** 다른 스레드에서 읽는다.
- 화면은 메인 스레드의 `poll_load` 에서만 바꾼다 (6ms 간격 확인).
- 읽는 동안 다른 경로로 사진이 열렸으면(`_load_seq`) 결과를 버린다. 읽는 동안 BBox·입력칸을 고쳤으면(`_edit_serial`) 편집을 지키려고 **이동을 취소**한다.
- 지나가는 사진이 깨졌으면 건너뛰고, 목적지 사진이 깨졌으면 안내하고 머문다.

### 마우스 판정 순서 (`on_mouse_down`)

1. 이동 모드 → 화면 이동
2. BBox 숨김 상태 → 안내만
3. (Shift 미입력) 선택된 BBox 의 핸들 위 → 크기 조절. 허용 거리는 화면 8px ÷ 배율
4. (Shift 미입력) BBox 안쪽 → 선택 + 이동 준비. 5px 이상 움직여야 이동으로 본다
5. 그 밖 → 새 BBox. 5px 미만은 클릭(선택), Class 4 는 만들지 않음

### 라벨 목록·Diff 표시

- 라벨 목록 상태: `원본` / `변경`(주황, diff 의 unchanged 가 아님) / `⚠ 확인`(빨강, [`box_problems`](../bbox/bbox_manager.md) 결과가 있음)
- Diff 를 켜면 추가 초록 · 수정 주황(원래 위치 회색 점선) · 삭제 빨강 점선으로 그린다.

### 렌더링 성능

- 화면에 보이는 영역만 잘라서(crop) 키운다. 4K 를 2000% 로 통째로 키우지 않는다.
- 많이 축소해서 볼 때는 `reduce(2/4/8)` 로 먼저 정수배 축소한다. 200% 이상 확대하면 `NEAREST` 로 픽셀 경계를 보여 준다.
- 창 크기 변경은 100ms 디바운스로 한 번만 다시 그린다.

## 단축키

전체 표는 [`help_dialog.SHORTCUT_GROUPS`](help_dialog.md) 에 있다. 입력칸(Entry)에 커서가 있으면 글자·숫자 단축키는 동작하지 않는다 (`is_typing`).

## 의존성

- **사용하는 것**: [`settings`](../settings.md), [`data_paths`](../data_paths.md), [`bbox_diff`](../bbox/bbox_diff.md), [`bbox_edit`](../bbox/bbox_edit.md), [`bbox_manager`](../bbox/bbox_manager.md), [`history`](../bbox/history.md), [`viewport`](../bbox/viewport.md), [`manifest_writer`](../manifest/manifest_writer.md), [`validator`](../validation/validator.md), [`coords`](../yolo/coords.md), [`yolo_loader`](../yolo/yolo_loader.md), [`yolo_writer`](../yolo/yolo_writer.md), 같은 폴더의 [`folder_drop`](folder_drop.md) · [`form_panel`](form_panel.md) · [`theme`](theme.md) · [`class_picker`](class_picker.md) · [`help_dialog`](help_dialog.md) · [`tooltip`](tooltip.md) · [`session`](session.md) · [`thumb_strip`](thumb_strip.md) · [`validation_dialog`](validation_dialog.md) · [`navigator`](navigator.md), Pillow
- **사용하는 곳**: [`main.py`](../../main.md), 화면 시험 [`day1_selftest`](../../tests/day1_selftest.md) · [`test_edit_ui`](../../tests/test_edit_ui.md) · [`test_filter_ui`](../../tests/test_filter_ui.md) · [`test_quick_review`](../../tests/test_quick_review.md) · [`test_step_hold`](../../tests/test_step_hold.md) · [`test_session`](../../tests/test_session.md) · [`test_label_io`](../../tests/test_label_io.md) · [`test_box_problems`](../../tests/test_box_problems.md) · [`test_manifest_edge`](../../tests/test_manifest_edge.md) · [`test_tooltip_help`](../../tests/test_tooltip_help.md)

## 주의사항

- **입력칸만 고친 뒤 Undo 하면 저장 확인을 건너뛸 수 있다.** `after_history` 는 `dirty` 를 BBox 목록만 보고(`boxes != _clean`) 다시 정한다. 그래서 검수 기록 칸을 고친 뒤 Undo/Redo 로 BBox 를 처음 상태로 돌리면 `dirty` 가 `False` 가 되고, 다음 사진으로 넘어갈 때 입력칸 변경이 묻지 않고 버려질 수 있다.
- 검수표 기록이 실패해도 TXT 는 이미 저장된 상태다. 사용자에게는 `dirty` 로 남겨 다시 저장하게 한다.
- RAW 밖에서 연 사진은 `data/work/_RAW밖/` 에 저장되고 검수표에는 기록되지 않는다. 같은 파일명이 여러 폴더에 있으면 이 폴더에서 덮어쓴다.
- 이 파일은 1,800줄이 넘는다. 계산 로직은 가능하면 `src/bbox`, `src/yolo` 처럼 화면 없는 모듈로 빼야 테스트하기 쉽다.
- 단축키를 바꾸면 [`help_dialog.SHORTCUT_GROUPS`](help_dialog.md) 도 같이 고쳐야 한다 ([`test_tooltip_help`](../../tests/test_tooltip_help.md) 가 확인).
