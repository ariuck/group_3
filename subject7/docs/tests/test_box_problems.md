# `tests/test_box_problems.py`

> 이상한 BBox(이미지 밖·Class 범위 밖 등) 찾기와 화면 표시 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_box_problems.py) · 대상: [`src/bbox/bbox_manager.box_problems`](../src/bbox/bbox_manager.md), [`src/ui/main_window`](../src/ui/main_window.md)

## 실행

```bash
python -m unittest tests/test_box_problems.py      # ProblemBoxUiTest 는 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `BoxProblemsTest` | 정상 BBox 는 문제 없음 · Class 범위 밖 · 사용 안 하는 Class · 이미지 밖 · 너무 작음 · 여러 문제 동시 보고 |
| `ProblemBoxUiTest` | 불러올 때 개수 안내 · 라벨 목록에서 이상한 것만 `⚠ 확인` · 좌표줄에 이유 표시 · 경고 이름표로 그림 · **자동으로 고치지 않고 남김** · Class 를 고치면 경고가 사라짐 |
