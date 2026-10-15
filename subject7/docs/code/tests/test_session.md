# `tests/test_session.py`

> 마지막 작업 위치 복원 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_session.py) · 대상: [`src/ui/session`](../src/ui/session.md), [`src/ui/main_window`](../src/ui/main_window.md)

## 실행

```bash
python -m unittest tests/test_session.py      # RestoreInAppTest 는 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `SessionFileTest` | 저장·불러오기 왕복 · 파일 없음 · 사라진 경로 무시 · 깨진 파일 무시 · 사진 없이는 저장 안 함 · 경로 두 개만 저장 + 임시 파일 안 남음 |
| `RestoreInAppTest` | 다시 켜면 이어서 시작 · 창으로 돌아오면 `Zone.Identifier` 정리 · 켜자마자 닫아도 예약된 복원이 오류를 내지 않음 (수정한 버그) · 기록 없으면 아무 일 없음 · 이미 연 것을 덮어쓰지 않음 · 지운 사진은 조용히 건너뜀 |
