# `tests/test_final_evidence.py`

> 최종본 증빙 시험. 가짜 `data/final` 폴더로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_final_evidence.py) · 대상: [`tools/final_evidence`](../tools/final_evidence.md)

## 실행

```bash
python -m unittest tests/test_final_evidence.py
```

## 시험 내용 (`FinalEvidenceTest`)

- 수량과 짝 계산
- 짝 없는 파일 개수
- 잘못된 라벨은 보고하고, Markdown 에 **파일명이 들어가지 않음**
- `split` 구조를 읽고 split 폴더까지 같아야 짝으로 봄
