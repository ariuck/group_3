# `tools/pack_results.py`

> 내 작업 결과(라벨 txt + 검수표)를 zip 하나로 묶어 팀원에게 전달하기 쉽게 한다. 내 검수 번호 범위만 골라 묶을 수 있다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tools/pack_results.py)

## 사용법

```bash
python tools/pack_results.py                                # 전부: data/share/결과_<시각>.zip
python tools/pack_results.py --name 김동훈 --from 1 --to 300  # 내 범위만: 결과_김동훈_<시각>.zip
python tools/pack_results.py -o 내결과.zip
```

번호는 프로그램 화면의 `N / 900` 과 같다 (데이터셋 → split → 파일명 순).

받는 쪽은 압축을 푼 뒤:

```bash
python tools/import_labels.py <푼 폴더> --apply
python tools/merge_manifests.py <푼 폴더>/검수표.csv --apply
```

## 담는 것 / 담지 않는 것

| 담음 | 담지 않음 |
|---|---|
| `data/work` 의 `.txt` (폴더 구조 유지) | 사진(jpg) |
| 검수표 → zip 안 `검수표.csv` (`--name` 이면 `검수표_<이름>.csv`) | `Zone.Identifier`, `_session.json` 등 라벨이 아닌 파일, 심볼릭 링크 |

`--from/--to` 를 주면 라벨과 검수표 줄 모두 그 범위만 담는다. 세 명의 결과를 한 곳에 풀어도 검수표 이름이 겹치지 않고, 내 범위 밖의 옛 라벨이 다른 사람이 고친 라벨을 덮어쓰지 못한다.

## 주요 구성요소

| 함수 | 설명 |
|---|---|
| `collect(work_dir)` | `(라벨 목록, 무시한 파일 수)` |
| `photo_numbers(raw_dir)` | `{(데이터셋, split, 사진 파일명): 번호}` — 화면 번호와 같은 순서 |
| `_label_key(work_dir, p)` | `<ds>/labels/<split>/<이름>.txt` → `(ds, split, stem)` |
| `pack(out_zip, work_dir, manifest_path, name, number_range, raw_dir)` | zip 생성. `{labels, manifest, skipped, out_of_range}` 반환. 범위가 1 ~ 사진 수 밖이면 `ValueError` |
| `main(argv)` | CLI. `--from`/`--to` 는 함께 써야 함. 담을 것이 없으면 빈 zip 을 지우고 종료 코드 2 |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md)
- **사용하는 곳**: 직접 실행, [`tools/share_server`](share_server.md) 웹 가이드의 안내 명령, [`tests/test_pack_results`](../tests/test_pack_results.md)

## 주의사항

- 폴더 구조가 다른 PC(예: `work/data/labels/파일.txt`)에서 저장된 라벨은 사진 이름으로 번호를 찾는다. 같은 이름이 RAW 에 하나뿐일 때만 범위에 넣는다.
- 검수표 CSV 는 엑셀에서 열리도록 BOM 이 붙은 UTF-8, 줄바꿈 `\r\n` 으로 쓴다.
- zip 은 회사 데이터다. 허용된 방법으로만 전달한다 (`data/` 는 `.gitignore`).
