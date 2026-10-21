# `subject8/scripts/plot_improvement.py`

> **kimchi_v4 기록용** — Baseline 과 개선 실험(exp001~003)을 같은 Dataset Version(kimchi_v4)·같은 Validation 에서 비교하는 표와 그림을 만든다. `results.csv` 와 학습 조건 문서만 읽으므로 사진·모델·GPU 가 없어도, 어느 PC 에서나 다시 만들 수 있다. v4 는 지난 Version 이라 입출력이 모두 `reports/history/kimchi_v4/` 에 있다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/plot_improvement.py)

## 사용법

```bash
cd subject8
python scripts/plot_improvement.py
```

| 입력 | 출력 (Git 에 올림) |
|---|---|
| `runs/<실행>/results.csv`, `reports/history/kimchi_v4/<실행>_training_condition.md` (학습 시간·GPU 메모리) | `reports/history/kimchi_v4/improvement_summary.csv`, `reports/history/kimchi_v4/figures/improvement_summary.svg` |

비교하는 실행은 코드 위쪽 `STEPS` 에 있다 (`baseline_v4`, `exp001_v4_imgsz1280`, `exp002_v4_imgsz1920`, `exp003_v4_imgsz1920_epoch100`).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `summarize(run, doc)` | best epoch(mAP50-95 최대)의 P·R·F1·mAP, 마지막 10 epoch 평균·표준편차, Val cls loss 최저 epoch, 마지막 Val/Train cls loss 비, 학습 시간·GPU 메모리 |
| `build()` | 네 실행을 요약하고 Baseline 대비·직전 단계 대비 변화량을 계산 |
| `write_csv(data)` | `improvement_summary.csv` (같은 폴더 `baseline_vs_improved.md` 의 숫자 근거) |
| `draw(data)` | 2×2 SVG: A. mAP50-95(best · 마지막10 평균), B. Precision·Recall·F1, C. epoch 별 Val mAP50-95 곡선, D. 학습 시간과 상승폭 |

## 의존성

- **사용하는 것**: 표준 라이브러리만 (`matplotlib` 불필요 — SVG 를 직접 쓴다)
- **사용하는 곳**: [`reports/history/kimchi_v4/baseline_vs_improved.md`](../../reports/history/kimchi_v4/baseline_vs_improved.md)

## 주의사항

- **마지막 10 epoch 평균·표준편차**는 epoch 사이 흔들림을 보려는 값이다. 한 단계의 상승폭이 이 표준편차와 비슷하면 우연일 수 있다.
- best epoch 는 Validation 으로 고른 값이라 약간 낙관적이다. 최종 성능은 Frozen Test(8일차)로만 말한다.
- 숫자는 학습 중 Validation 지표(`results.csv`)다. [실행·실험 가이드](../project/guides/training.md)의 공식 평가 값과 0.005 안팎 차이가 날 수 있다.
- 학습 조건 문서의 `걸린 시간`·`GPU 최대 사용 메모리` 줄 형식이 바뀌면 시간·메모리 칸이 비어 나온다.
- SVG 의 한글은 보는 PC 에 한글 글꼴이 있어야 제대로 보인다 (`Noto Sans CJK KR` → `Malgun Gothic` → `Apple SD Gothic Neo` 순으로 찾음).
