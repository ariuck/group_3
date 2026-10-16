# `src/ui/session.py`

> 마지막으로 열었던 폴더와 사진을 기억했다가, 프로그램을 다시 켜면 그 자리에서 이어서 시작하게 한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/ui/session.py)

## 역할

- 저장 위치: `data/work/_session.json` — `{"folder": ..., "image": ...}` 두 값뿐이다.
- WORK 안에 있어서 `.gitignore` 로 제외된다 (`data/**`).
- 라벨·검수표는 여기에 저장하지 않는다.

## 주요 구성요소

| 함수 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `session_path()` | – | `Path` | 호출할 때마다 `settings.WORK_DIR` 에서 계산 (테스트에서 폴더를 바꿔 쓰기 위해) |
| `save_session(folder, image)` | 폴더, 사진 | `bool` | 임시 파일 → 교체 (원자적). 실패해도 조용히 `False` |
| `load_session()` | – | `(folder, image)` 또는 `None` | 파일이 없거나 깨졌거나 경로가 사라졌으면 `None` |

## 의존성

- **사용하는 것**: [`settings`](../settings.md) (`WORK_DIR`)
- **사용하는 곳**: [`main_window`](main_window.md) (`apply_image` 에서 저장, `restore_session` 에서 읽기), [`tests/test_session`](../../tests/test_session.md)

## 주의사항

- 사진을 열 때마다 저장한다 (작은 파일 하나라 부담이 없다).
- 경로를 그대로 기록하므로 다른 PC 나 다른 위치로 저장소를 옮기면 복원되지 않는다 (조용히 건너뜀).
