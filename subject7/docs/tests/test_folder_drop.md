# `tests/test_folder_drop.py`

> 폴더 끌어다 놓기 도우미 시험. 화면 없이 경로 변환과 대상 고르기만 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_folder_drop.py) · 대상: [`src/ui/folder_drop`](../src/ui/folder_drop.md)

## 실행

```bash
python -m unittest tests/test_folder_drop.py
```

## 시험 내용

| 클래스 | 확인하는 것 |
|---|---|
| `ToLocalPathTest` | 보통 경로는 그대로 · `file://` 주소 해독 · 앞뒤 공백 제거 |
| `PickTargetTest` | 폴더 우선 · 폴더가 없으면 JPG · 쓸 것이 없으면 `None` |

`wslpath` 변환(Windows 경로 → WSL 경로)은 시험하지 않는다.
