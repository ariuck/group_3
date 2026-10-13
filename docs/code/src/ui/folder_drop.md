# `src/ui/folder_drop.py`

> 폴더·사진을 창에 **끌어다 놓기**(Drag & Drop). 선택 패키지 `tkinterdnd2` 가 있을 때만 켜지고, 없으면 이 기능만 꺼진다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/ui/folder_drop.py)

## 역할

- tkinter 에는 끌어다 놓기가 없어서 `tkinterdnd2` 를 쓴다 (`pip install tkinterdnd2`).
- Windows 탐색기에서 WSL 의 창으로 끌어다 놓으면 Windows 경로가 들어오므로 `wslpath` 로 WSL 경로로 바꾼다.

## 주요 구성요소

| 함수 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `make_root()` | – | Tk 루트 | `TkinterDnD.Tk()` 를 시도하고, 실패하면 일반 `tk.Tk()` |
| `drop_available(widget)` | 위젯 | `bool` | 끌어다 놓기를 쓸 수 있는가 |
| `register_drop(widget, callback)` | 위젯, 콜백 | `bool` | 놓으면 `callback([경로, ...])` |
| `to_local_path(text)` | 놓은 항목 문자열 | 경로 문자열 | `file:///…` → 보통 경로, `C:\…` · `\\wsl.localhost\…` → `wslpath -u` 결과 |
| `pick_target(paths)` | 경로 목록 | `("folder" \| "image", Path)` 또는 `None` | 폴더가 있으면 첫 폴더, 없으면 첫 JPG |

## 의존성

- **사용하는 것**: `tkinterdnd2` (선택), `wslpath` (WSL 에서만)
- **사용하는 곳**: [`main_window`](main_window.md) (`make_root`, `register_drop`, `pick_target`), [`tests/test_folder_drop`](../../tests/test_folder_drop.md)

## 주의사항

- `tkinterdnd2` 는 `requirements.txt` 필수 항목이 아니다. 없어도 `[폴더 열기]` 버튼은 동작한다.
- `wslpath` 가 없는 환경(일반 Windows Python)에서는 경로를 바꾸지 않고 그대로 쓴다.
