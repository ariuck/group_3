# `tests/test_import_labels.py`

> 라벨 가져오기 시험. 가짜 raw/work 폴더로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_import_labels.py) · 대상: [`tools/import_labels`](../tools/import_labels.md)

## 실행

```bash
python -m unittest tests/test_import_labels.py
```

## 시험 내용 (`ImportLabelsTest`)

- 새 라벨은 맞는 데이터셋·split 으로 들어감
- `Zone.Identifier` 는 무시하고 새로 만들지도 않음
- 미리보기는 아무것도 복사하지 않음
- 같은 내용은 충돌이 아니고, 다른 내용은 보류
- unknown · invalid · ambiguous 는 보고만 하고 복사 안 함
- 경로 힌트(데이터셋·split 폴더 이름)로 같은 이름 구분
- RAW 는 절대 바뀌지 않음
- `--overwrite` 없이 적용하면 옛 라벨이 남고 크게 경고
- `--overwrite` 는 옛 라벨을 바꾸고 백업
- 다른 폴더의 같은 이름 파일도 백업에서 살아남음 (`_2` 번호)
- 덮어쓴 것이 없으면 백업 안 만듦
- 명령줄 미리보기 · 폴더가 없을 때
