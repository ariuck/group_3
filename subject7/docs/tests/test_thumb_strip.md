# `tests/test_thumb_strip.py`

> 하단 사진 목록(썸네일 줄)과 검수표 상태 읽기 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_thumb_strip.py) · 대상: [`src/ui/thumb_strip`](../src/ui/thumb_strip.md), [`src/manifest/manifest_writer.read_status_map`](../src/manifest/manifest_writer.md)

## 실행

```bash
python -m unittest tests/test_thumb_strip.py      # ThumbStripTest 는 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `StatusMapTest` | 파일이 없으면 빈 dict · 상태 맵과 찾기 · 모르는 사진·RAW 밖은 빈칸 |
| `ThumbStripTest` | 보이는 칸 수가 너비를 따름 · 제목에 개수 · 현재 사진을 보이게 옮기고 강조 · 보이는 범위 안 이동은 스크롤 안 함 · 클릭하면 번호 알림 · 미리보기는 나중에 읽고 기억 · **넘기는 동안은 미리보기를 기다림** (성능) · 가까운 것부터 읽음 · 사진 아래 표시 · `‹ ›` 는 한 화면씩 · 깨진 사진도 목록은 유지 · 빈 목록 |
