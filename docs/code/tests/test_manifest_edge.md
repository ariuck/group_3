# `tests/test_manifest_edge.py`

> 검수표(CSV) 기록의 까다로운 상황 시험 — 빈 파일 · 엑셀로 저장한 파일 · 특수 글자 · 검수일 · 경고창 반복.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_manifest_edge.py) · 대상: [`src/manifest/manifest_writer`](../src/manifest/manifest_writer.md), [`src/ui/main_window.load_form`](../src/ui/main_window.md)

## 실행

```bash
python -m unittest tests/test_manifest_edge.py      # ManifestWarningUiTest 는 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 | 비고 |
|---|---|---|
| `ManifestEdgeTest` | 0바이트 파일은 새 검수표로 봄 | 수정한 버그 (저장이 완전히 막히던 문제) |
| | 공백만 있는 파일도 새 검수표 · 머리글이 다르면 거부하고 파일 불변 · 엑셀식 BOM + CRLF 허용 · 칸이 모자라거나 남는 줄도 저장 가능 · cp949 파일은 도움말 있는 오류 | |
| | 검수를 마친 상태가 되면 검수일 자동 기입 | 수정한 문제 (손으로 적어야 하던 문제) |
| | 모든 완료 상태에 검수일 · 이미 적힌 날짜는 안 바꿈 · 기본값은 오늘 | |
| | 특수 글자 보존 · 다른 위치의 같은 파일명은 다른 줄 · 다시 저장하면 줄 갱신 + 원본 수 유지 · 사람이 정한 `수정 필요` 유지 · RAW 밖은 기록 안 함 | |
| `ManifestWarningUiTest` | 깨진 검수표 경고창은 파일마다 한 번만 · 파일을 고친 뒤 새 문제가 생기면 다시 경고 | |
