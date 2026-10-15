# `tests/test_tooltip_help.py`

> 말풍선(Tooltip)과 단축키 도움말(F1) 시험. 도움말에 적힌 단축키가 실제로 연결되어 있는지도 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_tooltip_help.py) · 대상: [`src/ui/tooltip`](../src/ui/tooltip.md), [`src/ui/help_dialog`](../src/ui/help_dialog.md), [`src/ui/main_window`](../src/ui/main_window.md)

## 실행

```bash
python -m unittest tests/test_tooltip_help.py      # 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `TooltipTest` | 지연 후 보이고 나가면 숨김 · 클릭하면 숨김, 빨리 지나가면 안 보임 · `cancel_all` 이 예약·표시 모두 제거 (수정한 문제: 창 닫기 시험이 가끔 실패) · 글자 대신 함수 가능, 빈 글자는 안 보임 · 두 번 보여도 창이 쌓이지 않음 |
| `HelpDialogTest` | **도움말의 모든 키가 실제로 연결됨** — 코드를 바꾸고 도움말을 안 고치면 여기서 잡힘 · 모든 묶음이 있고 한 번만 열림 · `F1` 과 `도구` 메뉴로 열림 · 도구 줄 버튼에 말풍선 |
