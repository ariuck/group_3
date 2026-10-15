# `tests/test_data_paths.py`

> RAW/WORK 경로 처리 시험 (화면 없음).

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_data_paths.py) · 대상: [`src/data_paths`](../src/data_paths.md)

## 실행

```bash
python -m unittest tests/test_data_paths.py
```

## 시험 내용 (`DataPathsTest`)

| 확인하는 것 | 비고 |
|---|---|
| 검증 결과 경로로 사진을 찾을 때 이름이 아니라 **전체 경로**로 찾음 | 수정한 버그 |
| 대문자 `.JPG` 와 `.jpeg` 도 찾음 | 수정한 버그 |
| 없으면 `None` · Windows 식 `\` 구분자 | |
| 출처 판별과 WORK 경로가 같은 구조 · RAW 밖은 `_RAW밖/` | |
| `Zone.Identifier` 는 지우고 라벨은 남김 · WORK 폴더 안만 정리 · WORK 폴더가 없어도 오류 없음 | |
