# `main.py`

> 프로그램 시작 파일. `src/ui/main_window.py` 의 `main()` 을 불러 라벨링 화면을 띄운다.

[← 코드 문서 목차](README.md) · [코드 보기](../../main.py)

## 역할

- 저장소 맨 위에서 `python main.py` 한 줄로 프로그램을 실행할 수 있게 한다.
- 이 파일이 저장소 루트에 있어야 `from src...` 형태의 import 가 동작한다 (루트가 `sys.path` 에 들어감).

## 사용법

```bash
python main.py
```

## 의존성

- **사용하는 것**: [`src/ui/main_window.py`](src/ui/main_window.md) 의 `main()`
- **사용하는 곳**: 없음 (진입점)

## 주의사항

- `src/` 안의 파일을 직접 실행(`python src/ui/main_window.py`)하면 `src` 패키지를 찾지 못한다. 항상 루트에서 `main.py` 로 실행한다.
