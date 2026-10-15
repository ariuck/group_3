# `src/ui/hangul_input.py`

> 입력칸 안에서 쓰는 **두벌식 한글 조합기**. WSL 의 tkinter 에는 한글 입력기가 없어서, 영문 자판 글자(r, k, s …)를 받아 프로그램이 직접 한글로 조합한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/ui/hangul_input.py)

## 역할

- 검수 기록의 작성자·검수자·발견된 문제·비고 칸에 한글을 쓸 수 있게 한다.
- 한/영 전환: `한/영` 키(`Hangul` 또는 `Alt_R` 으로 들어옴), `Shift+Space`, 입력칸 위 `[한/영]` 버튼
- Windows 쪽 입력기는 **영어(A)** 상태로 두고 쓴다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `CHO`, `JUNG`, `JONG` | 초성 19 · 중성 21 · 종성 28(빈 받침 포함) |
| `KEYMAP` | 두벌식 자판 영문 → 자모. 대문자 `Q W E R T O P` 는 쌍자음·ㅒ·ㅖ |
| `VOWEL_PAIRS` / `FINAL_PAIRS` | 겹모음(ㅗ+ㅏ→ㅘ) / 겹받침(ㄹ+ㄱ→ㄺ) 과 그 역방향 표 |
| `jamo_for(char)` | 영문 한 글자 → 자모. 그 밖의 대문자는 소문자와 같게 (Caps Lock 대비) |
| `Composer` | 한 음절 조합 상태. `.add(jamo)` → 확정된 글자 반환, `.text()`, `.backspace()`, `.reset()`, `.active` |
| `compose(keys)` | 시험용. `compose("rkskek") == "가나다"` |
| `TOGGLE_KEYSYMS` | `{"Hangul", "Alt_R"}` |
| `MODIFIER_KEYSYMS` | Shift·Ctrl 등. 이 키를 눌렀다고 조합을 끊지 않음 (`혜` 를 칠 때 Shift 를 먼저 누르므로) |
| `HangulIME(on_mode_change)` | 여러 입력칸이 공유하는 한/영 상태 |
| `.attach(entry)` | 입력칸에 키 이벤트 연결 |
| `.bind_global(root)` | 이미지 화면에 커서가 있어도 한/영 키로 미리 바꿀 수 있게 창 전체에 연결 |
| `.toggle()`, `.finish()` | 전환 / 조합 중인 글자 확정 |

### 조합 규칙 (`Composer`)

- 초성+중성 뒤 자음 → 받침. 받침 뒤 자음이 겹받침이 되면 합침.
- 받침 뒤 모음 → 받침(겹받침이면 뒤쪽)이 다음 글자 초성으로 넘어감 (`갑` + `ㅏ` → `가바`).
- 조합 중 Backspace → 한 단계씩 지움 (겹모음·겹받침은 반으로).

## 의존성

- **사용하는 것**: `tkinter`, `time`
- **사용하는 곳**: [`form_panel`](form_panel.md), [`tests/test_hangul_input`](../../tests/test_hangul_input.md)

## 주의사항

- **한/영 키 중복 신호 처리**: 꾹 누르면 신호가 반복되고, Windows 가 누름 신호를 가로채 떼는 신호만 오는 경우도 있다. 그래서 0.15초 안의 반복은 한 번으로 치고, 누름 기록이 없거나 1초 넘게 지난 떼는 신호는 전환으로 처리한다.
- `Ctrl`·`Alt` 와 함께 누른 키(붙여넣기 등)는 조합하지 않는다.
- 커서를 옮기거나 다른 칸을 클릭하면 조합 중이던 글자는 그대로 확정된다.
- 화면 시험(`test_hangul_input`)은 WSL 창의 포커스 타이밍 때문에 간혹 실패한다 (README 의 알려진 제한사항).
