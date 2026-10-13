# `tools/import_labels.py`

> 팀원에게 받은 라벨(TXT)을 내 작업 폴더(`data/work`)로 가져온다. 넣을 데이터셋·split 은 `data/raw` 의 같은 이름 사진으로 찾는다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tools/import_labels.py)

## 사용법

```bash
python tools/import_labels.py <받은 폴더>                     # 미리보기 (복사 안 함)
python tools/import_labels.py <받은 폴더> --apply              # 새 라벨만 복사
python tools/import_labels.py <받은 폴더> --apply --overwrite  # 내용이 다른 것도 덮어씀 (덮어쓰기 전 백업)
```

전체 흐름은 [team/결과_주고받기](../../team/결과_주고받기.md) 와 [`pack_results`](pack_results.md) · [`merge_manifests`](merge_manifests.md) 를 함께 본다.

## 분류 결과

| 종류 | 뜻 | `--apply` 시 |
|---|---|---|
| `new` | WORK 에 없는 새 라벨 | 복사 |
| `same` | 이미 같은 내용 | 그대로 |
| `conflict` | 이름은 같고 내용이 다름 | `--overwrite` 일 때만 덮어씀 |
| `unknown` | RAW 에 같은 이름 사진이 없음 | 건너뜀 |
| `ambiguous` | 같은 이름 사진이 여러 곳 + 받은 경로로도 못 정함 | 건너뜀 |
| `invalid` | Validation `CRITICAL` (Class·좌표 범위 등) | 건너뜀 |

`.txt` 가 아닌 파일(`Zone.Identifier` 등)은 세기만 하고 무시한다.

## 주요 구성요소

| 함수 | 설명 |
|---|---|
| `build_index(raw_dir)` | `{사진 이름(확장자 없음): [(데이터셋, split)]}` |
| `_choose(candidates, parts)` | 후보가 여럿이면 받은 파일 경로의 폴더 이름(데이터셋, split)으로 좁힘 |
| `plan_import(source, raw_dir, work_dir)` | 위 표의 분류 결과 + `_ignored` 개수. 복사하지 않음 |
| `apply_import(result, overwrite, backup_dir)` | 복사한 개수 반환. `backup_dir` 가 있으면 덮어쓰기 전 파일을 먼저 복사 |
| `main(argv)` | CLI. `--overwrite` 로 덮어쓰면 `data/backup/라벨_가져오기_교체전_<시각>/` 에 백업 |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), [`src/validation/validator`](../src/validation/validator.md) (`parse_label_file`, `validate_rows`)
- **사용하는 곳**: 직접 실행, [`tests/test_import_labels`](../tests/test_import_labels.md), [`tests/test_pack_results`](../tests/test_pack_results.md)

## 주의사항

- **백업 폴더 구조가 설명과 다르다.** `apply_import` docstring 은 "작업 폴더와 같은 하위 경로로" 백업한다고 하지만, 실제로는 백업 폴더 바로 아래에 **파일 이름만으로** 저장하고 이름이 겹치면 `_2`, `_3` 을 붙인다. 되돌릴 때 원래 데이터셋·split 은 파일 이름으로 다시 찾아야 한다.
- `--overwrite` 없이 실행하면 내용이 다른 라벨은 **복사하지 않는다**. 옛 라벨이 남아 있으면 새 라벨이 하나도 안 들어오는 것처럼 보이므로 화면에 큰 경고를 낸다.
- 복사는 `shutil.copyfile`(내용만)이라 Windows 의 `Zone.Identifier` 정보가 따라오지 않는다.
- Class 번호 `2.0` 같은 표기는 validator 기준으로 `BAD_NUMBER` → `invalid` 로 분류된다.
