# `tools/export_manifest_xlsx.py`

> 검수표 CSV 를 엑셀 틀(`manifests/dataset_manifest.xlsx`)의 `검수표` 시트에 채워 **제출용 xlsx** 를 만든다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tools/export_manifest_xlsx.py)

## 사용법

```bash
pip install openpyxl                                   # 이 도구에서만 쓰는 선택 설치
python tools/export_manifest_xlsx.py                   # data/final/dataset_manifest.xlsx
python tools/export_manifest_xlsx.py -o 내파일.xlsx
```

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `TEMPLATE` | `manifests/dataset_manifest.xlsx` (고치지 않음) |
| `INT_COLUMNS` | 숫자로 넣을 칸: No, 원본 BBox 수, 최종 BBox 수, TXT 줄 수 = 화면 BBox 수 |
| `export(csv_path, template, out_path)` | 틀의 머리글 순서대로 CSV 값을 채움. 틀에 있는 칸이 CSV 에 없으면 `ValueError`. 선택 목록(데이터 유효성 검사)을 마지막 줄까지 늘림. 채운 줄 수 반환 |
| `main(argv)` | openpyxl 이 없으면 설치 안내 후 종료 코드 2 |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), `openpyxl` (선택)
- **사용하는 곳**: 직접 실행, [`tests/test_export_manifest_xlsx`](../tests/test_export_manifest_xlsx.md)

## 주의사항

- 틀의 선택 목록은 원래 200행까지만 걸려 있어서, 900행이 모두 선택 목록을 쓰도록 범위를 늘린다.
- 결과에는 실제 사진 파일명이 들어간다. 기본 저장 위치 `data/` 는 `.gitignore` 대상이다. `-o` 로 다른 곳에 저장하면 Git 에 올리지 않도록 주의한다.
- 빈 값은 엑셀에서 빈 칸(`None`)으로 넣는다.
