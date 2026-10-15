# `src/ui/form_panel.py`

> 오른쪽 아래 **검수 기록** 입력칸. 상태·이미지 유형은 눌러서 고르는 칩, 작성자·검수자·발견된 문제·비고는 글자 칸이다. 칸 이름은 검수표 머리글과 같다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/form_panel.py)

## 역할

- 사람이 판단해서 채우는 칸을 받아 [`record_save(human=...)`](../manifest/manifest_writer.md) 로 넘긴다.
- 사진을 열 때는 검수표 값을 다시 채워 보여 준다.
- WSL 에서도 한글을 칠 수 있게 [`HangulIME`](hangul_input.md) 를 붙인다.
- 작성자·검수자 이름을 프로그램이 켜져 있는 동안 기억해서 빈 칸에만 미리 채운다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `SCENE_CHOICES` | 김치+대상 객체 · 정상 김치 · 대상 객체 단독 · 판단 어려움 ([manifest_guide](../../standards/manifest_guide.md) 와 같은 값) |
| `FIELDS` | (머리글, 화면 이름, 종류, 선택지, 빈 값 버튼 이름). 상태의 빈 값 = `자동`, 이미지 유형의 빈 값 = `미정` |
| `CHIP_COLUMNS` | 3 — 칩을 한 줄에 몇 개씩 놓을지 |
| `REMEMBERED` | `작성자`, `검수자` |
| `FormPanel(parent, on_change, on_mode, on_submit)` | `tk.Frame` 카드 |
| `.get_values()` | `{머리글: 값}` (앞뒤 공백 제거) |
| `.set_values(row)` / `.clear()` | 검수표 한 줄로 채움. 채우는 동안에는 `on_change` 를 부르지 않음 |
| `.fill_remembered()` | 비어 있는 작성자·검수자 칸에만 기억한 이름을 채움. 다른 칸에 같은 이름이 있으면 채우지 않음 (자기 사진 자기 검수 방지). 채운 것은 변경으로 보지 않음 |
| `.choose_scene(index)` | `Ctrl+1~4` 로 이미지 유형 선택 |
| `.focus_field(key, select_all=False)` | 글자 칸에 커서 두기 (`R` 키 뒤 `발견된 문제`) |
| `.flash(key, ms=1600)` | 선택 칸을 빨간 테두리로 잠깐 깜빡임 (이미지 유형 미선택 안내) |
| `.stop()` | 창을 닫을 때 깜빡임 예약 취소 |
| `.ime` | 공유 [`HangulIME`](hangul_input.md). 제목줄의 `[한/영]` 버튼과 연결 |

콜백: `on_change` = 사람이 값을 바꿈 → 저장 안 됨 표시 / `on_mode` = 한/영 전환 알림 / `on_submit` = 글자 칸에서 Enter.

## 의존성

- **사용하는 것**: [`manifest_writer.STATUS_CHOICES`](../manifest/manifest_writer.md), [`theme`](theme.md), [`hangul_input.HangulIME`](hangul_input.md)
- **사용하는 곳**: [`main_window`](main_window.md), [`tests/test_form_panel`](../../tests/test_form_panel.md)

## 사용 예

```python
self.form = FormPanel(side, on_change=self.on_form_changed, on_submit=self.on_form_submit)
self.form.set_values(read_human(image_path))      # 사진을 열 때
msg = record_save(image_path, raw_txt, work_txt, len(boxes), human=self.form.get_values())
```

## 주의사항

- 이름 기억은 **메모리에만** 있다. 프로그램을 끄면 사라지고 파일에 저장하지 않는다.
- `get_values()` 는 모든 칸을 문자열로 돌려준다 (`None` 없음). 그래서 저장할 때 빈 칸은 "지움"으로 기록된다. 입력칸을 다시 채운 뒤 저장하는 흐름이라 정상 동작이다.
- 칩 선택지는 검수표 머리글·상태 목록과 **글자가 정확히 같아야** 한다. 바꾸려면 [`manifest_writer`](../manifest/manifest_writer.md) 와 [manifest_guide](../../standards/manifest_guide.md) 를 함께 고친다.
