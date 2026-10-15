# `tests/test_pack_results.py`

> 결과 묶기 시험. 가짜 폴더로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_pack_results.py) · 대상: [`tools/pack_results`](../tools/pack_results.md) (+ [`tools/import_labels`](../tools/import_labels.md) 왕복)

## 실행

```bash
python -m unittest tests/test_pack_results.py
```

## 시험 내용 (`PackResultsTest`)

| 확인하는 것 | 비고 |
|---|---|
| 라벨과 검수표만 들어감 · 폴더 구조와 내용 유지 · 입력 불변 · 검수표나 work 폴더가 없어도 동작 | |
| 묶은 것을 풀어 `import_labels` 로 받으면 같은 라벨이 들어옴 | 왕복 시험 |
| 번호 범위면 그 범위의 라벨·줄만 | |
| 폴더 구조가 다른 PC(`work/data/labels/파일.txt`)의 라벨도 사진 이름으로 번호를 찾아 묶음 | 실제로 있었던 일 |
| 같은 이름이 두 곳에 있으면 추측하지 않음 · 세 명의 범위를 한곳에 풀어도 겹치지 않음 | |
| 잘못된 범위 거부 · `--from`/`--to` 는 함께 · 묶을 것이 없으면 알리고 거부 | |
