# `subject8/scripts/plot_runs.py`

> 모든 학습 실행(`runs/*/results.csv`)의 학습 곡선과 같은 Dataset Version 끼리의 비교 그래프, 요약표를 만든다. 사진·모델 없이 Git 에 있는 기록만으로 다른 PC 에서도 그대로 다시 만들 수 있다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/plot_runs.py)

## 사용법

```bash
cd subject8
python scripts/plot_runs.py                                   # results.csv 가 있는 실행 전부
python scripts/plot_runs.py --runs baseline_v4 exp001_v4_imgsz1280
```

| 입력 | 출력 (Git 에 올림) |
|---|---|
| `runs/<실행>/results.csv`, `runs/<실행>/args.yaml`, `models/` (보관된 Weight), `reports/**/<실행>_training_condition.md` | `reports/figures/runs/<실행>.png` (실행당 약 0.1MB), `reports/figures/comparison/runs_comparison_<Dataset Version>.png`, `reports/runs_summary.csv`, **`models/README.md`** (모델 목록) |

`models/README.md`: Version 별 표 — 실행 · 공식 여부(`baseline_best.pt`·`final_best.pt` 가 가리키는 실행) · Weight 링크 · imgsz · epoch · batch · best epoch Val P·R·mAP50·mAP50-95 · 학습 조건 기록 · 그래프(학습 곡선 · Confusion Matrix · PR 곡선) 링크. 공식 Version 이 맨 위.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `dataset_version(run_name)` | 실행 이름의 `_v<N>` → `kimchi_v<N>`. `smoke*` 는 `smoke`(비교에서 제외), 규칙에 안 맞으면 `unknown` |
| `best_row(rows)` | mAP50-95 최대 epoch (Ultralytics 8.4 best.pt 기준과 같음) |
| `plot_run(name, rows, args, out)` | 2×3 그림: box·cls·dfl Loss(train/val), Val Precision/Recall, Val mAP50, Val mAP50-95 (best epoch 점·값 표시). 제목에 Dataset Version 과 학습 조건 |
| `plot_comparison(version, data, out)` | 같은 Version 실행들의 Val mAP50-95 곡선 + best 값 막대 |
| `condition_doc(run)` | 학습 조건 기록 찾기 (공식 Baseline 은 `reports/02_baseline/baseline_training_condition.md`) |
| `write_models_readme(summary)` | `models/README.md` 작성 |
| `main()` | 실행별 그림 → Version 별 비교 → `runs_summary.csv`(`run, dataset_version, model, imgsz, epochs, batch, optimizer, lr0, seed, epochs_done, best_epoch, precision, recall, map50, map50_95`) → `models/README.md` |

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/constants`](../src/constants.md) (`DEFAULT_DATASET_VERSION`), `matplotlib`, `PyYAML`
- **사용하는 곳**: 직접 실행 (새 학습 후 커밋 전에)

## 주의사항

- **비교는 같은 Dataset Version 끼리만** 묶는다. Version 이 다르면 Validation 사진이 달라 점수를 직접 비교할 수 없다 (예: `baseline_v1` 은 Val 84장, `kimchi_v4` 실행은 Val 132장).
- 새 실행 이름에는 반드시 `_v<N>` 을 넣는다. 없으면 `unknown` 으로 묶인다.
- 타일링 실행(`tile2x2`)의 학습 중 Val 은 조각 단위라 Version 비교 그래프에서 빼고, 표에는 `(조각 Val)` 로 표시한다. 원본 사진 단위 비교는 `reports/…/tiling_eval.csv`.
- 숫자는 학습 중 Validation 지표(results.csv)다. 공식 평가는 [`07_evaluate_baseline`](07_evaluate_baseline.md) 처럼 Weight 로 따로 한다.
- PNG 메타데이터에 날짜·버전을 넣지 않아, 기록이 같으면 다시 그려도 파일이 바뀌지 않는다 (불필요한 Git 변경 없음).
