# `tests/test_export_manifest_xlsx.py`

> 검수표 엑셀 내보내기 시험. `openpyxl` 이 없으면 건너뛴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_export_manifest_xlsx.py) · 대상: [`tools/export_manifest_xlsx`](../tools/export_manifest_xlsx.md)

## 실행

```bash
python -m unittest tests/test_export_manifest_xlsx.py
```

## 시험 내용 (`ExportXlsxTest`)

- 숫자 칸은 숫자로 채움
- 선택 목록을 마지막 줄까지 늘림
- 틀 파일은 바뀌지 않음
- 틀에 있는 칸이 CSV 에 없으면 알려 줌
