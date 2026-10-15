# `src/ui/thumb_strip.py`

> 화면 아래 **이미지 목록(썸네일 줄)**. 현재 사진 주변의 미리보기를 가로로 보여 주고, 누르면 그 사진으로 이동한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/thumb_strip.py)

## 역할

- 창 너비에 맞춰 보이는 칸 수가 바뀐다 (2~16칸).
- 현재 사진은 파란 바탕으로 강조한다.
- 사진 아래에 저장 여부(✓)와 검수 상태를 색 글자로 보여 준다 (`mark_of` 콜백).
- 제목줄에 작업 진행 요약과 보기 필터를 넣을 자리(`header`)를 제공한다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `THUMB_W, THUMB_H` | 128 × 72 |
| `MAX_CELLS` / `CACHE_LIMIT` | 미리 만들어 두는 칸 16개 / 기억하는 미리보기 150장 (오래된 것부터 버림) |
| `IDLE_MS` | 220 — 마지막 이동 후 이만큼 조용해야 미리보기를 읽기 시작 |
| `make_thumbnail(path)` | JPG 를 `draft` 로 작게 읽어 축소. 깨진 파일은 회색 상자 |
| `ThumbStrip(parent, on_select, mark_of=None)` | |
| `.set_files(files, total_all=None)` | 목록 교체. 필터 중이면 제목에 `12개 / 전체 900개` |
| `.set_current(index)` | 현재 사진. 보이는 범위 밖이면 가운데쯤 오도록 이동 |
| `.refresh_marks()` | 저장·상태가 바뀐 뒤 글자 다시 계산 |
| `.page(direction)` | `‹ ›` 버튼 — 한 화면씩 넘김 (현재 사진은 그대로) |
| `.header`, `.summary`, `.hint` | 제목줄 위젯 (main_window 가 필터 콤보박스를 붙임) |
| `.stop()` | 예약된 읽기·크기 조정 작업 취소 |

## 동작 방식

- 아직 읽지 않은 미리보기는 회색 상자로 먼저 보여 주고 대기열에 넣는다.
- 대기열은 **현재 사진에 가까운 것부터** 한 번에 한 장씩 읽는다. 그 사이 화면이 반응한다.
- 방향키로 빠르게 넘기는 동안에는 읽기를 미룬다 (`_poke` 디바운스). 한 장 읽기가 약 50ms 라 이동이 끊겨 보이지 않게 하기 위해서다.
- `mark_of` 결과는 `refresh_marks()` 나 `set_files()` 때만 다시 계산한다.

## 의존성

- **사용하는 것**: [`theme`](theme.md), Pillow
- **사용하는 곳**: [`main_window`](main_window.md), [`tests/test_thumb_strip`](../../tests/test_thumb_strip.md)

## 주의사항

- 미리보기 캐시는 경로를 키로 쓴다. 같은 경로의 사진 파일이 바뀌어도 프로그램을 다시 켤 때까지 옛 미리보기가 보일 수 있다.
- `CURRENT_BG` 는 import 시점의 `theme.COLORS["accent"]` 값이다. 실행 중에 테마 색을 바꿔도 이 값은 바뀌지 않는다.
