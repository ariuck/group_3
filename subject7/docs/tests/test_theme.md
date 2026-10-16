# `tests/test_theme.py`

> 디자인 체계(theme)와 Class 선택 위젯 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_theme.py) · 대상: [`src/ui/theme`](../src/ui/theme.md), [`src/ui/class_picker`](../src/ui/class_picker.md)

## 실행

```bash
python -m unittest tests/test_theme.py      # 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `ThemeTest` | `setup` 이 글꼴을 고르고 스타일을 정의 · 버튼 크기가 글자에 맞음 · 색이 올바른 hex 값 · 카드에 테두리 · 모든 사용자 스타일로 위젯 생성 가능 |
| `ClassPickerTest` | 모든 Class 표시 + 현재 Class 강조 · 클릭하면 Class 번호 알림 · `set` 은 강조만 바꿈 · 사용 안 하는 Class 는 회색 |
