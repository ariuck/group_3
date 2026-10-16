# `tests/test_label_io.py`

> 라벨 파일 읽기 시험 (BOM · 형식이 다른 줄 · 읽지 못한 줄 경고).

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_label_io.py) · 대상: [`src/yolo/yolo_loader`](../src/yolo/yolo_loader.md), [`src/validation/validator.parse_label_file`](../src/validation/validator.md), [`src/ui/main_window`](../src/ui/main_window.md)

## 실행

```bash
python -m unittest tests/test_label_io.py      # UnreadableLinesUiTest 는 화면(Tk) 필요
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `LabelReadTest` | **BOM 무시** (수정한 버그: 첫 줄을 통째로 못 읽던 문제) · Class `2.0` 처럼 정수인 실수는 받아 줌 · 줄바꿈 종류와 빈 줄 · 읽지 못한 줄은 숨기지 않고 셈 · 빈 파일은 오류 아님 |
| `UnreadableLinesUiTest` | 경고가 이미지 위에 계속 보임 · 저장 전에 묻고 거절하면 아무것도 안 씀 · 확인하면 읽은 줄만 저장하고 한 번만 물음 · 원본 라벨 불변 · 깨끗한 사진은 묻지 않음 |
