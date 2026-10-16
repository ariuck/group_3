# `subject8/src/registry.py`

> 모델 등록부 — 실행 이름 하나로 Weight 위치 · Dataset Version · 학습 조건(imgsz 등) · 타일링 여부를 찾는다. 스크립트마다 모델 경로나 imgsz 를 따로 적지 않게 한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../src/registry.py)

## 규칙

| 무엇 | 위치 |
|---|---|
| 공식 Version 실행의 Weight | `models/baseline/<실행>.pt` (`baseline*`) · `models/improved/<실행>.pt` (그 밖) |
| 지난 Version 실행의 Weight | `models/history/<Version>/<실행>.pt` |
| 공식 Baseline (산출물 2) | `models/baseline/baseline_best.pt` = `OFFICIAL["baseline"]` 의 복사본 |
| Final Model (산출물 4, 8일차) | `models/final/final_best.pt` = `OFFICIAL["final"]` 의 복사본 |

공식 Version 은 [`constants.DEFAULT_DATASET_VERSION`](constants.md), 공식 실행은 이 파일의 `OFFICIAL` 한 곳에서 정한다. 전체 목록은 [`models/README.md`](../../models/README.md) ([`plot_runs`](../scripts/plot_runs.md) 가 만듦).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `OFFICIAL` | `{"baseline": "baseline_v5", "final": None}` |
| `ALIASES` | 가이드 이름 경로 (`baseline_best.pt`, `final_best.pt`) |
| `run_version(run)` | 실행 이름의 `_v<N>` → `kimchi_v<N>` |
| `run_role(run)` | `baseline` · `improved` |
| `weight_path(run)` | 이 실행의 Weight 를 보관할 위치 (위 규칙) |
| `find_weight(run)` | 보관된 Weight — 정해진 위치에 없으면 `models/` 아래 같은 이름을 찾고, 없으면 `FileNotFoundError` |
| `resolve(name)` | `baseline` · `final` · 실행 이름 · `.pt` 경로 → `(Weight 경로, 실행 이름)` |
| `run_args(run)` | `runs/<실행>/args.yaml` |
| `run_tiles(run)` | `tile2x2` 가 이름에 있으면 `((2, 2), 0.2)`, 아니면 `None` |

## 의존성

- **사용하는 것**: [`src/constants`](constants.md) (`DEFAULT_DATASET_VERSION`), `PyYAML`
- **사용하는 곳**: [`scripts/07`](../scripts/07_evaluate_baseline.md), [`08`](../scripts/08_predict_images.md), [`09`](../scripts/09_collect_failures.md), [`plot_runs`](../scripts/plot_runs.md)

## 주의사항

- 실행 이름에 `_v<N>` 이 없으면 `ValueError` (smoke 실행은 등록부에 넣지 않는다).
- 공식 Version 을 바꾸면 Weight 의 정해진 위치도 바뀐다 (공식 ↔ history 이동은 한 번에 정리).
