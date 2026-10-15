# `subject8/scripts/03_build_split.py`

> 교과 8 학습용 데이터 분할(방안 B)을 만든다. 촬영 시각으로 18개 묶음을 정하고 묶음 단위로 train / val / test / bridge_holdout 을 배정한 뒤, Manifest CSV · `configs/dataset.yaml` · `reports/01_data/dataset_summary.csv` 를 만든다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/03_build_split.py)

## 사용법

```bash
cd subject8
python scripts/03_build_split.py                 # Manifest·설정·요약만 (kimchi_v4 — 라벨 수정본 필요)
python scripts/03_build_split.py --copy-files    # data/yolo, data/bridge_holdout 에 실제 파일까지 복사
python scripts/03_build_split.py --version kimchi_v1 --copy-files   # 이전 분할 재현
```

| 옵션 | 설명 |
|---|---|
| `--copy-files` | 실제 파일 배치까지 |
| `--version` | `kimchi_v4`(기본) · `kimchi_v3` · `kimchi_v2` · `kimchi_v1`. 블록 분할 규칙은 [`constants.py` 의 `BLOCK_RULES`](../src/constants.md). `kimchi_v3`·`v4` 는 라벨 수정본이 필요 ([`04_import_label_fixes`](04_import_label_fixes.md) 먼저) |

분할 정책 설명: `subject8/docs/project/split_policy.md`

## 처리 순서

1. `data/subject7_final/검수표.csv` 로드
2. [`assign_capture_groups`](../src/split_builder.md) — 파일명 시각 기준 5분 넘게 벌어지면 새 묶음 (G00~G17)
3. [`assign_splits`](../src/split_builder.md) — 방안 B 배정
4. `manifests/split_manifest.csv` + 역할별 `train.csv` · `val.csv` · `test.csv` · `bridge_holdout.csv`
5. `configs/dataset.yaml`
6. `reports/01_data/dataset_summary.csv`
7. split × 이미지 유형 교차표 출력
8. (`--copy-files`) 실제 파일 배치

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `PROJECT_ROOT` | `subject8/` |
| `main()` | 위 순서 실행 |

## 의존성

- **사용하는 것**: [`subject8 src/split_builder`](../src/split_builder.md) (`SplitBuilder`), [`subject8 src/constants`](../src/constants.md) (`BLOCK_RULES`, `DATASET_VERSIONS`, `DEFAULT_DATASET_VERSION`), `pandas`
- **사용하는 곳**: 직접 실행

## 주의사항

- **`--copy-files` 는 `data/yolo` 와 `data/bridge_holdout` 을 통째로 지우고 다시 만든다** (`clean=True`). 그 안에 직접 넣어 둔 파일이 있으면 사라진다.
- `manifests/*.csv` 와 `reports/01_data/dataset_summary.csv` 는 버전과 관계없이 같은 이름으로 덮어쓴다. 버전을 바꿔 실행한 뒤 학습하면 [`06`](06_train_baseline.md) 의 precheck 는 통과하지만, 이전 실험과 Val 구성이 달라진다.
- 묶음 수(18)·G00(50장)·G17(150장)이 맞지 않으면 `assert` 로 중단된다. 이 데이터셋 전용 스크립트다.
- [`02_audit`](02_audit_subject7_final.md) 와 마찬가지로 `src` 패키지 이름이 저장소 루트와 겹치므로 `python scripts/03_build_split.py` 형태로 실행한다.
