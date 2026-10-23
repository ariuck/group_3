# `tools/check_docs.py`

> 코드와 문서가 1:1로 대응하는지 점검한다. 문서가 빠진 `.py` 와, 코드가 사라졌는데 남은 `.md` 를 찾는다. 교과 8 폴더도 같은 규칙으로 점검할 수 있다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tools/check_docs.py)

## 사용법

```bash
python tools/check_docs.py               # subject7 (이 폴더에서)
python tools/check_docs.py ../subject8   # subject8
```

```
[subject7] 점검 완료: 코드 N개 · 문서 없음 0개 · 코드 없는 문서 0개
```

문제가 있으면 목록을 보여 주고 **종료 코드 1** 을 돌려준다. 커밋 전에 돌리면 된다.

## 규칙

- `<경로>/<이름>.py` → `docs/<경로>/<이름>.md` (과목 폴더 기준, 코드와 같은 경로)
- 내용이 없는 `__init__.py` 는 문서를 만들지 않는다.
- `docs/project/`에는 기준서·설계·팀 운영 문서도 함께 있다. 그래서 "코드 없는 문서"는 **코드가 있는 폴더와 같은 이름의 docs 하위 폴더**(`docs/src/`, `docs/tools/`, `docs/tests/`, 교과 8 은 `docs/scripts/`) 안에서만 찾는다.
- 설정 파일 설명서(예: `configs/dataset.yaml` → `docs/configs/dataset.md`)를 두더라도, 같은 이름의 원본 파일이 있으면 정상으로 본다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `ROOT` | 기본 점검 폴더 (`subject7/`) |
| `SKIP_DIRS` | 점검하지 않는 폴더: `.git`, `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `data`, `docs`, `runs`, `private`(Git 제외 개인 자료 — 예: 발표자료의 `private/tools/`), `.vscode`, `.idea` |
| `code_files(root)` | 문서가 있어야 하는 `.py` 상대 경로 |
| `_has_source(root, doc_rel)` | 문서와 같은 경로·이름의 원본 파일(확장자 무관)이 있는가 |
| `check(root)` | `(코드 목록, 문서 없음, 코드 없는 문서)` |
| `main(argv)` | 인자로 받은 과목 폴더(없으면 `ROOT`)를 점검하고 종료 코드 반환 |

## 의존성

- **사용하는 것**: 표준 라이브러리 `pathlib`, `sys`
- **사용하는 곳**: 직접 실행

## 주의사항

- 파일이 **있는지만** 본다. 문서 내용이 코드와 맞는지는 사람이 확인해야 한다.
- 코드 파일 이름을 바꾸거나 옮기면 문서도 같은 경로로 옮겨야 "문서 없음 1 + 코드 없는 문서 1" 이 사라진다.
- `docs/` 바로 아래 문서(`main.md` 등)는 "코드 없는 문서" 검사에서 빠진다 (주제 문서와 구분할 수 없음). `main.py` 를 없애면 `docs/main.md` 는 직접 지운다.
- 주제별 폴더 이름을 코드 폴더 이름(`src`, `tools`, `tests`, `scripts` …)과 같게 만들면 그 안의 문서가 "코드 없는 문서"로 잡힌다.
