# `src/ui/navigator.py`

> 사진 목록 · 이전/다음 · 진행률 · 보기 필터 관리. 화면 코드가 없는 순수 로직이다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/navigator.py)

## 역할

- `all_files` = 폴더에서 찾은 사진 전체, `files` = 지금 보이는 사진 (필터를 건 경우 걸러진 것)
- 이전/다음·번호·진행률은 모두 **`files`(보이는 목록) 기준**이다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `IMAGE_EXTS` | `{".jpg", ".jpeg"}` |
| `_natural_key(p)` | `img2` 가 `img10` 보다 앞에 오는 자연 정렬 |
| `ImageNavigator()` | 속성: `folder`, `all_files`, `files`, `index`(0부터), `predicate`, `current` |
| `.load_folder(folder)` | 폴더 바로 아래 JPG, 없으면 하위 폴더까지(`images/train`, `images/val` …) 찾음. 폴더별로 묶고 이름순. 첫 사진 반환 (없으면 `None`). 필터 해제 |
| `.set_current(path)` | 현재 사진 지정. 필터에 걸러진 사진이면 필터를 풀고, 목록에 없는 사진이면 그 폴더를 새로 스캔 |
| `.set_filter(predicate)` | `predicate(path) → bool` (None = 전체). 보이는 개수 반환. 현재 사진이 걸러지면 `index = -1` |
| `.filtered`, `.total` | 필터 여부 / 보이는 개수 |
| `.has_prev()`, `.has_next()`, `.prev_path()`, `.next_path()` | 이동 가능 여부와 경로 |
| `.jump_to_index(index)` | 0부터 세는 번호의 경로 (범위 밖이면 `None`) |
| `.progress_text()` | `"21 / 300"` (없으면 `"0 / 0"`) |

## 의존성

- **사용하는 것**: 없음 (`re`, `pathlib`)
- **사용하는 곳**: [`main_window`](main_window.md), [`tests/test_navigator`](../../tests/test_navigator.md)

## 사용 예

```python
nav = ImageNavigator()
first = nav.load_folder("data/raw/이물검출_학습데이터1")    # images/train 의 사진 전체
nav.set_current(first)
nav.set_filter(lambda p: status_of(p, status_map) == "수정 필요")
print(nav.progress_text())
```

## 주의사항

- `prev_path()` / `next_path()` 는 경로만 알려 준다. 번호는 `set_current()` 를 불러야 바뀐다.
- `load_folder` 는 폴더 바로 아래에 사진이 **한 장이라도** 있으면 하위 폴더를 보지 않는다.
- `IMAGE_EXTS` 를 [`settings.IMAGE_EXTS`](../settings.md) 와 따로 갖고 있다. 확장자를 바꿀 때 둘 다 고친다.
