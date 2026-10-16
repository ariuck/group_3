# `src/ui/validation_dialog.py`

> QA 검증(Validation) 결과 창. CRITICAL / WARNING / INFO 개수를 요약하고 결과를 표로 보여 준다. 행을 더블클릭하면 그 사진으로 이동한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/validation_dialog.py)

## 역할

- [`validator.validate_dataset`](../validation/validator.md) 결과(`report`)를 사람이 보기 좋게 보여 준다.
- 심각도별로 글자 색을 다르게 한다 (CRITICAL 빨강 · WARNING 주황 · INFO 파랑).
- 더블클릭한 행의 `relative_path` 를 `on_jump` 콜백으로 넘긴다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `ValidationDialog(parent, report, csv_path=None, on_jump=None)` | `tk.Toplevel`. 980×540 |
| `._build_ui()` | 위: 총 건수 + 심각도별 개수 + 안내 / 가운데: 표(심각도·코드·파일·줄·내용) + 스크롤바 / 아래: 닫기 |
| `._on_double_click()` | `on_jump(relative_path)` 호출. 예외가 나면 경고창 |
| `show_validation_dialog(parent, report, csv_path, on_jump)` | 생성 도우미 |

## 의존성

- **사용하는 것**: `tkinter`, `ttk`, `messagebox`
- **사용하는 곳**: [`main_window.run_validation`](main_window.md) — `on_jump` 로 [`data_paths.find_raw_image`](../data_paths.md) 를 거쳐 사진을 연다

## 주의사항

- 다른 화면과 달리 [`theme`](theme.md) 를 쓰지 않고 글꼴(`Malgun Gothic`)과 색을 직접 지정한다. 한글 글꼴이 없는 WSL 에서는 다른 글꼴로 보일 수 있다.
- 결과가 수천 건이어도 한 번에 표에 넣는다.
