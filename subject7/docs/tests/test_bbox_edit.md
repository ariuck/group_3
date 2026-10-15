# `tests/test_bbox_edit.py`

> BBox 이동·크기 조절 계산 시험 (화면 없음).

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_bbox_edit.py) · 대상: [`src/bbox/bbox_edit`](../src/bbox/bbox_edit.md)

## 실행

```bash
python -m unittest tests/test_bbox_edit.py
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `HandleTest` | 핸들 8개와 커서 이름 · 허용 거리 안 판정 · 아주 작은 BBox 에서는 가장 가까운 핸들 |
| `MoveTest` | 크기 유지 + 원본 dict 불변 · 이미지 가장자리에서 멈춤 |
| `ResizeTest` | 핸들마다 해당 변만 움직임 · 반대쪽 변을 넘지 못함 · 이미지 안 유지 · 가장자리의 작은 BBox 를 안쪽으로 키움 · 원본 불변 |
