# `src/data_paths.py`

> RAW / WORK 폴더 구조 처리. 원본(RAW)을 보호하고, 수정한 라벨은 RAW 와 **같은 폴더 구조**의 WORK 에만 저장하게 한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../src/data_paths.py)

## 역할

```
RAW :  data/raw/이물검출_학습데이터2/images/validation/a.jpg     ← 읽기만
WORK:  data/work/이물검출_학습데이터2/labels/validation/a.txt    ← 수정한 라벨 (여기에만 저장)
```

- 경로에서 **데이터셋 이름과 split** 을 뽑아낸다. 이 두 값이 곧 검수표의 `출처 데이터셋` / `원래 split` 이다.
- 저장 경로가 RAW 안인지 검사하는 데 쓰는 `is_inside` 를 제공한다.
- WSL 로 복사할 때 생기는 `Zone.Identifier` 찌꺼기 파일을 정리한다.

## 주요 구성요소

| 함수 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `is_inside(child, parent)` | 경로 2개 | `bool` | `child` 가 `parent` 폴더 안인가 (실제 경로 `resolve()` 기준) |
| `locate_in_raw(image_path)` | 이미지 경로 | `(dataset, split)` | RAW 밖이면 `(None, None)`. `<ds>/images/<split>/a.jpg` 가 아니면 `(ds, "")` |
| `work_label_path(image_path)` | 이미지 경로 | `Path` | `WORK/<ds>/labels/<split>/<stem>.txt`. RAW 밖 이미지는 `WORK/_RAW밖/<stem>.txt` |
| `remove_zone_markers(work_dir=None)` | WORK 경로 | 지운 개수 | 이름이 `Zone.Identifier` 로 끝나는 **일반 파일만** WORK 안에서 삭제 |
| `find_raw_image(rel_path)` | `'DS2/validation/a'` | `Path` 또는 `None` | 검증 결과의 상대 경로로 RAW 이미지를 정확히 찾는다 (`.JPG` 대문자 포함) |

## 의존성

- **사용하는 것**: [`src/settings.py`](settings.md) (`RAW_DIR`, `WORK_DIR`, `IMAGE_EXTS`)
- **사용하는 곳**: [`manifest/manifest_writer`](manifest/manifest_writer.md) (`locate_in_raw`), [`ui/main_window`](ui/main_window.md) (전부), [`tests/day1_selftest`](../tests/day1_selftest.md), [`tests/test_data_paths`](../tests/test_data_paths.md), [`tests/test_edit_ui`](../tests/test_edit_ui.md)

## 사용 예

```python
from src.data_paths import locate_in_raw, work_label_path, is_inside
from src import settings

img = settings.RAW_DIR / "이물검출_학습데이터1/images/train/a.jpg"
locate_in_raw(img)            # ('이물검출_학습데이터1', 'train')
out = work_label_path(img)    # data/work/이물검출_학습데이터1/labels/train/a.txt
assert not is_inside(out, settings.RAW_DIR)
```

## 주의사항

- 경로는 **호출할 때마다** `settings` 에서 읽는다. 테스트에서 `settings.RAW_DIR` 을 바꿔 쓰기 위해서다.
- `find_raw_image` 는 파일 이름만으로 찾지 않고 `데이터셋/split/이름` 전체를 쓴다. 다른 데이터셋·split 에 같은 이름이 있어도 엉뚱한 사진을 열지 않게 하기 위해서다.
- RAW 밖에서 연 이미지는 저장은 되지만(`_RAW밖/`) 출처를 알 수 없어서 검수표에는 기록되지 않는다.
- `remove_zone_markers` 는 WORK 밖이나 심볼릭 링크는 건드리지 않는다. 지우지 못한 파일은 조용히 넘어간다.
