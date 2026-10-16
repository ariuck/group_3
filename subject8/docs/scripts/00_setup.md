# `subject8/scripts/00_setup.py`

> 올인원 준비 — 처음 받은 PC 든 이미 준비된 PC 든 **같은 명령 하나**로 가상환경 → 교과 7 복원 → 데이터 점검 → `kimchi_v4`·`kimchi_v5` 학습 폴더까지 만든다. 이미 된 단계는 건너뛴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/00_setup.py)

## 사용법

```bash
# 각 PC 에서 한 번: 회사 원본 폴더를 그대로 subject7/data/raw/ 에 복사
#   subject7/data/raw/이물검출_학습데이터1/…, 이물검출_학습데이터2/…
cd ~/group_3/subject8
python3 scripts/00_setup.py             # 언제 실행해도 같은 결과
python3 scripts/00_setup.py --rebuild   # 학습 폴더를 지우고 다시 복사
```

| 단계 | 하는 일 | 이미 되어 있으면 |
|---|---|---|
| 1 | Python 3.14 인지 확인 (아니면 설치 방법을 알려 주고 멈춤). `.venv` 가 없거나 설치가 끝나지 않았으면(`.venv/.requirements_installed` 에 `requirements.txt` 해시가 없음) 설치 → 이후 `.venv` Python 으로 다시 실행 | 건너뜀 |
| 2 | `subject7/data/raw` 사진 900장 확인 | 모자라면 넣을 위치를 알려 주고 멈춤 |
| 3 | [`subject7 tools/restore_from_final.py`](../../../subject7/docs/tools/restore_from_final.md) `--apply` — work · 검수표 · final 사진 | 같은 파일은 건너뜀, 다른 파일은 덮어쓰지 않고 멈춤 |
| 4 | [`02_audit_subject7_final`](02_audit_subject7_final.md) | 매번 (몇 초) |
| 5 | v4·v5 마다 [`03_build_split`](03_build_split.md) 로 manifest → 학습 폴더가 manifest·라벨과 다를 때만 `--copy-files` | 복사 건너뜀 |
| 6 | `git status` 로 manifest · 점검 보고서 · `subject7/data/final` 이 Git 과 같은지 | 다르면 목록을 보여 주고 종료 코드 1 |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `check_python(version, where)` | Python 3.14 가 아니면 deadsnakes 설치 방법을 알려 주고 멈춤 (`REQUIRED_PYTHON`) |
| `install_done()` | `INSTALL_MARKER`(`.venv/.requirements_installed`)에 지금 `requirements.txt` 해시가 있는가 — 설치가 중간에 실패한 `.venv` 를 걸러 냄 |
| `ensure_venv()` | `.venv` 준비(필요하면 설치 후 표시 기록) 후 `os.execv` 로 자신을 `.venv` Python 으로 다시 실행 |
| `check_raw()` | RAW 사진 수 확인 (`EXPECTED_IMAGES = 900`) |
| `dataset_matches(version)` | 학습 폴더의 사진(크기)·라벨(내용)이 manifest·라벨 수정본과 같고, manifest 에 없는 파일이 없는가 |
| `main()` | 위 단계 실행. 실패하면 그 명령을 보여 주고 멈춤 |

## 의존성

- **사용하는 것**: [`src/split_builder`](../src/split_builder.md), `02`·`03` 스크립트, `subject7/tools/restore_from_final.py`, `git`
- **사용하는 곳**: 직접 실행 (README "다른 PC 에서 시작하기")

## 주의사항

- 시스템 `python3` 로 시작해도 된다 (3.14 확인). `.venv` 설치는 torch 때문에 처음 한 번 몇 분 걸린다.
- 이 PC(이미 준비됨)에서 약 7초, `--rebuild` 는 사진 복사 때문에 수 분.
- 학습은 하지 않는다. 모델은 Git 의 `models/` 에 있으므로 바로 평가·예측할 수 있다.
