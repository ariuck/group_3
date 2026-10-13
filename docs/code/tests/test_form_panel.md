# `tests/test_form_panel.py`

> 검수 기록 입력칸(칩 버튼 + 글자 칸) 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_form_panel.py) · 대상: [`src/ui/form_panel`](../src/ui/form_panel.md)

## 실행

```bash
python -m unittest tests/test_form_panel.py      # 화면(Tk) 필요
```

## 시험 내용 (`FormPanelTest`)

| 묶음 | 확인하는 것 |
|---|---|
| 선택 칸 | 모든 선택지가 라디오로 보임 · 처음엔 빈칸 · 누르면 값 설정 + 변경 알림 · `자동`·`미정` = 빈 값 |
| 이름 기억 | 직접 쓴 이름이 다음 사진 빈 칸에 채워짐 · 이미 적힌 이름은 절대 안 바꿈 · 자기 사진에 자기를 검수자로 채우지 않음 · 미리 채우기는 변경이 아니고 기억도 안 바꿈 · 손으로 지우면 기억 중단 · 다른 칸은 기억 안 함 |
| 값 읽고 쓰기 | `set_values` 는 변경 알림 없이 채움 · 글자 입력은 변경 알림 · `clear` · 모르는 값·`None` 은 빈칸 · 한/영 버튼 존재 |
