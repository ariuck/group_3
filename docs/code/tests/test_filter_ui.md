# `tests/test_filter_ui.py`

> 상태별 보기 필터 화면 시험 (사진 6장 + 검수표 몇 줄).

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_filter_ui.py) · 대상: [`src/ui/main_window`](../src/ui/main_window.md) (필터), [`src/ui/navigator`](../src/ui/navigator.md)

## 실행

```bash
python -m unittest tests/test_filter_ui.py      # 화면(Tk) 필요
```

## 시험 내용 (`FilterUiTest`)

| 확인하는 것 | 비고 |
|---|---|
| 처음엔 전체 · 상태로 거르면 첫 해당 사진으로 · `미작업` = 검수표에 없음 · 현재 사진이 해당하면 그대로 | |
| 이전/다음이 걸러진 목록을 따름 · 해당 없으면 안내 후 전체로 | |
| 해당 없는 필터 뒤 위쪽 번호·총 개수가 이전 값으로 남지 않음 | 수정한 버그 |
| 저장 확인을 취소하면 번호 표시 복원 · 전체로 돌아가기 · 숨겨진 사진을 열면 필터 표시 해제 · 미저장 변경 취소 시 모두 유지 · 아무것도 안 열었으면 무시 | |
