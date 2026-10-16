# `tools/merge_manifests.py`

> 팀원들의 검수표(CSV)를 하나로 합친다. 사진 1장 = 1줄, 키 = 이미지 파일명 + 출처 데이터셋 + 원래 split.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tools/merge_manifests.py)

## 사용법

```bash
python tools/merge_manifests.py 나.csv 동훈.csv 혜성.csv      # 미리보기
python tools/merge_manifests.py 받은폴더                       # 폴더 안 *.csv 전부
python tools/merge_manifests.py 받은폴더 --apply               # manifests/dataset_manifest.csv 에 저장
python tools/merge_manifests.py ... --apply -o 합친결과.csv --raw <원본 폴더>
```

## 합치는 규칙

1. **출처 바로잡기**: 출처 데이터셋·split 이 비었거나 `data/raw` 에 없는 값(팀원 PC 의 폴더 이름 등)이면, 사진 이름으로 RAW 에서 찾아 고친다. 그래도 모르면 알려 주고 **저장하지 않는다**.
2. **같은 내용**(No 를 뺀 모든 칸이 같음) → 하나로
3. **충돌**(내용이 다름) → ① `검수 전` 이 아닌 줄 ② 검수일이 늦은 줄 ③ 뒤에 넣은 파일의 줄 순으로 고르고 화면에 알린다
4. 출처 데이터셋 · split · 파일명 순으로 정렬하고 No 를 1부터 다시 매긴다
5. 저장할 파일이 이미 있으면 **입력에 없어도 자동으로 함께 합치고**, 덮어쓰기 전 같은 폴더에 `<이름>.백업-<시각>.csv` 를 남긴다

## 주요 구성요소

| 함수 | 설명 |
|---|---|
| `key_of(row)`, `_same(a, b)`, `_rank(row)` | 키 / 같은 내용인가 / 충돌 시 우선순위 |
| `load_inputs(paths)` | 파일·폴더 → `[(경로, 줄 목록)]`. [`manifest_writer._load`](../src/manifest/manifest_writer.md) 로 읽어 머리글(19칸)·인코딩을 검사 |
| `raw_name_index(raw_dir)` | `{사진 파일명: [(데이터셋, split)]}` |
| `normalize_sources(loaded, raw_index)` | 출처를 바로잡음 (줄을 직접 고침). `(바로잡은 수, 알 수 없는 줄)` 반환 |
| `merge(loaded)` | `(합친 줄, 충돌 목록, 같은 줄 수)` |
| `summarize(rows, raw_dir)` | 상태별 수, 작성자 빈 줄, 작성자=검수자 줄, 미처리 REVIEW, RAW 중 검수표에 없는 사진 수 |
| `main(argv)` | CLI |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), [`src/manifest/manifest_writer`](../src/manifest/manifest_writer.md) (`HEADERS`, `STATUS_*`, `ManifestError`, `_load`, `_save`)
- **사용하는 곳**: 직접 실행, [`tests/test_merge_manifests`](../tests/test_merge_manifests.md)

## 주의사항

- 엑셀에서 `CSV (쉼표로 분리)` 로 저장한 cp949 파일이나 머리글이 다른 파일은 **어느 파일인지 알리고 중단**한다. `CSV UTF-8` 로 다시 저장해야 한다.
- 충돌 시 "검수일이 늦은 줄" 비교는 글자 비교다. 날짜를 `2026-10-08` 형식으로 적어야 올바르게 비교된다.
- `manifest_writer` 의 이름이 `_` 로 시작하는 내부 함수(`_load`, `_save`)를 가져다 쓴다. 그 함수의 동작을 바꾸면 이 도구도 함께 확인한다.
- 결과는 회사 데이터다 (`manifests/*.csv` 는 `.gitignore`).
