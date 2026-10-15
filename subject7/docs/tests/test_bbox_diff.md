# `tests/test_bbox_diff.py`

> RAW ↔ 지금 BBox 비교 시험 (화면 없음).

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_bbox_diff.py) · 대상: [`src/bbox/bbox_diff`](../src/bbox/bbox_diff.md)

## 실행

```bash
python -m unittest tests/test_bbox_diff.py
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `IouTest` | IoU 계산 |
| `DiffTest` | 변화 없음 · 반올림 오차는 그대로 · 추가/삭제 · 이동·크기 변경은 수정 · Class 만 바꿔도 수정 · 멀리 옮기면 삭제+추가 · 가장 많이 겹치는 쌍끼리 짝 · 빈 목록 · 요약 문장 |
