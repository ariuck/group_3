# `tests/test_qa_summary.py`

> QA Summary 만들기 시험. 가짜 폴더로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_qa_summary.py) · 대상: [`tools/qa_summary`](../tools/qa_summary.md)

## 실행

```bash
python -m unittest tests/test_qa_summary.py
```

## 시험 내용 (`QaSummaryTest`)

- 추가 · 수정 · 삭제 · 그대로 개수
- Class 별 전후 합계
- Markdown 에 핵심 숫자가 있고 **파일명은 없음**
- 미처리 REVIEW 와 작성자=검수자는 FAIL 로 보고
- 입력 불변

코드에 고정된 문장(사람 이름, Human QA 결과 등)은 시험하지 않는다.
