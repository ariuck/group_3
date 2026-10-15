# `tools/build_final.py`

> 검수가 끝난 사진과 라벨을 `data/final` 로 정리해 **최종본(FINAL Dataset)** 을 만든다. 조건을 하나라도 못 채우면 만들지 않는다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tools/build_final.py)

## 사용법

```bash
python tools/build_final.py                       # 미리보기 (조건 확인 + 장수)
python tools/build_final.py --apply               # 실제로 만든다
python tools/build_final.py --apply --overwrite   # 이미 있으면 data/backup 으로 옮기고 다시 만든다
python tools/build_final.py --layout flat|nested  # 다른 폴더 구조
```

### 만드는 것 (기본 `split`)

```
data/final/
├── images/train/*.jpg · images/validation/*.jpg     RAW 사진 복사
├── labels/train/*.txt · labels/validation/*.txt     data/work 의 검수 라벨 (없으면 RAW 라벨)
├── classes.txt                                      Class 0~6 이름, 한 줄에 하나
└── 검수표.csv                                       들어간 사진의 검수표 줄 (출처 데이터셋 확인용)
```

| `--layout` | 구조 |
|---|---|
| `split` (기본) | `images/<split>/`, `labels/<split>/` — 원래 train/validation 유지, 데이터셋 폴더는 합침 |
| `flat` | `images/`, `labels/` 한 폴더 |
| `nested` | `<데이터셋>/images/<split>/` — 원래 폴더 그대로 |

어느 구조든 train/validation 을 **새로 나누거나 섞지 않는다** (교과 8 에서 결정).

### 만들기 전 조건 (`check`)

- 모든 RAW 사진이 검수표에 있고, 상태가 `검수 완료` 또는 `수정 완료`
- 검수자 칸이 채워져 있고 작성자와 다름
- 라벨이 있음 (WORK 또는 RAW)
- `split`·`flat` 구조에서 사진 이름이 겹치지 않음
- Validation `CRITICAL` 0건

## 주요 구성요소

| 함수 | 설명 |
|---|---|
| `collect_photos(raw_dir)` | `[(데이터셋, split, 사진 경로)]` 정렬 |
| `label_source(raw, work, ds, split, stem)` | `(라벨 경로, RAW 를 썼는가)` — WORK 우선 |
| `check(raw_dir, work_dir, manifest_path, layout)` | `{items, blocked, validation, raw_labels, rows, header}`. `blocked` 가 비어야 만들 수 있음 |
| `existing_content(final_dir)` | `.gitkeep` 을 뺀 기존 파일 수 |
| `build(result, final_dir, overwrite, backup_dir, classes, layout)` | 복사 후 파일 크기 비교로 확인, `classes.txt`·`검수표.csv` 작성 |
| `summarize(result)` | 데이터셋/split 별 장수 |
| `main(argv)` | CLI. 막히면 이유별 장수와 예시 5개를 보여 주고 종료 코드 1 |

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), [`src/validation/validator`](../src/validation/validator.md) (`validate_dataset`)
- **사용하는 곳**: 직접 실행, [`tests/test_build_final`](../tests/test_build_final.md)

## 주의사항

- RAW 와 `data/work` 는 읽기만 한다. `data/final`·`data/backup` 은 회사 데이터라 Git 에 올라가지 않는다.
- **RAW 의 모든 사진이 조건을 채워야 만든다.** `검수 전`·`수정 필요`·`제외` 사진은 건너뛰는 것이 아니라 `blocked` 로 잡혀 최종본 전체가 만들어지지 않는다. 그래서 `제외` 사진이 한 장이라도 있으면 만들 수 없다. (README §14 의 "`제외` 사진은 최종본에 넣지 않습니다" 는 "그런 사진이 있으면 만들지 않는다"는 뜻으로 읽어야 한다.) Validation 도 RAW 전체를 검사한다.
- `--overwrite` 없이 `data/final` 에 파일이 있으면 만들지 않는다. 덮어쓸 때는 기존 내용을 `data/backup/final_교체전_<시각>/` 으로 **옮긴다** (지우지 않음).
- `classes.txt` 에는 [`settings.CLASSES`](../src/settings.md) 의 이름을 그대로 쓴다 (`enabled: false` 인 Class 4 도 번호를 지키기 위해 포함).
