# `tools/final_evidence.py`

> 최종본(`data/final`)을 읽어 **증빙 숫자**(폴더 구조·수량·짝·자체 Validation·Class 분포·대표 TXT)를 Markdown 으로 만든다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tools/final_evidence.py)

## 사용법

```bash
python tools/final_evidence.py            # 화면에 미리보기
python tools/final_evidence.py --apply    # reports/final_evidence_auto.md 로 저장
```

사람이 캡처를 넣어 정리한 `reports/final_evidence.md` 는 덮어쓰지 않는다. 이 도구의 결과는 그 캡처가 가리키는 숫자의 근거다.

## 주요 구성요소

| 함수 | 설명 |
|---|---|
| `inspect(final_dir)` | 이미지·라벨 수, 짝(`split/이름` 까지 같아야 짝), split 별 수량, 빈 TXT, Class 별 BBox, Validation 이슈, 대표 TXT 3개(BBox 수가 서로 다른 것), `classes.txt`·`검수표.csv` 유무 |
| `build_markdown(info, today)` | 6개 장: 폴더 구조 · 수량과 짝 · 최종본 자체 검사 · Class 별 BBox · 대표 YOLO TXT · 화면 캡처 안내 |
| `main(argv)` | CLI |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), [`src/validation/validator`](../src/validation/validator.md) (`parse_label_file`, `validate_rows`)
- **사용하는 곳**: 직접 실행, [`tests/test_final_evidence`](../tests/test_final_evidence.md)

## 주의사항

- **사진 파일명은 넣지 않는다** (회사 데이터). 대표 TXT 예시도 내용(숫자)만 넣는다.
- `split`·`flat` 구조를 가정한다. `nested` 로 만든 최종본은 `images/` 가 없어서 0장으로 나온다.
- 6장의 캡처 담당자 이름이 코드에 고정되어 있다.
