# `tests/test_viewport.py`

> Zoom·편집 시험 — 확대·이동 좌표 계산과 Undo/Redo. 화면 없이 순수 계산만 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_viewport.py) · 대상: [`src/bbox/viewport`](../src/bbox/viewport.md), [`src/bbox/history`](../src/bbox/history.md)

## 실행

```bash
python tests/test_viewport.py           # 직접 실행형 (OK / FAIL 출력)
python -m pytest tests/test_viewport.py # pytest 로도 실행 가능
```

## 시험 내용

| 대상 | 시험 |
|---|---|
| `Viewport` | 기본값은 항등 변환 · 어떤 상태에서도 좌표 왕복 · 확대해도 커서 지점 고정 · 확대 후 축소하면 원래대로 · 최소·최대 배율 · Pan · 큰 이미지 맞춤 + 가운데 · 작은 이미지는 키우지 않음 · `upscale` · BBox 변환과 잘라내기 · **다른 배율에서 그려도 이미지 좌표가 같음** (저장 YOLO 좌표 불변) |
| `History` | Undo/Redo 기본 · 새 편집은 Redo 비움 · 스냅샷은 독립 사본 · 같은 상태 중복 무시와 개수 제한 · `clear` |

함수형 시험(`test_*`)이라 unittest 클래스가 없다. [`run_all`](run_all.md) 은 직접 실행형으로 돌린다.
