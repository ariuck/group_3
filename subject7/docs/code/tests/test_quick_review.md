# `tests/test_quick_review.py`

> 한 키 검수(`Enter` = 이상 없음 · `R` = 수정 필요 · `N` = 미작업으로) · 저장 안 됨 표시 · 작업 진행 요약 · 이미지 유형 확인 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_quick_review.py) · 대상: [`src/ui/main_window`](../src/ui/main_window.md), [`src/ui/form_panel`](../src/ui/form_panel.md)

## 실행

```bash
python -m unittest tests/test_quick_review.py      # 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `QuickReviewTest` | `Enter` → 검수 완료 + 저장 + 다음 · 고친 뒤 `Enter` → 수정 완료 · 검수자 이름이 다음 사진 빈 칸에 이어지되 적힌 이름은 안 바꿈 · 마지막 사진은 저장 후 머무름 · 사진이 없으면 아무 일 없음 · `R` → 수정 필요 + 이유 칸 준비 · 이미 쓴 이유 유지 · 이유 칸 `Enter` → 저장 후 다음 · 키 연결 · `N` 다음 미작업 / 처음으로 순환 / 모두 작업됨 |
| | 저장 결과 메시지가 마우스를 움직여도 남음 (수정한 문제) · 일정 시간 뒤 좌표 안내 다시 · 다른 메시지가 없으면 안내 계속 갱신 · 새 메시지는 항상 교체 |
| | `● 저장 안 됨` 표시가 변경을 따라감 · 작업 진행 요약 · 사진이 없으면 요약 비움 |
| `SceneTypeTest` | 이미지 유형이 비면 `Enter` 로 안 넘어감 · 고르면 동작하고 기록됨 · `Ctrl+1~4` 로 네 유형 · 이유 칸 `Enter` 도 확인 · `W`·`Ctrl+S` 는 막지 않음 · 이미 고른 유형 유지 · 종료 시 깜빡임 예약이 남지 않음 |
