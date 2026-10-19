# `subject8/scripts/16_evaluate_final_test.py`

> Final Model 의 **Frozen Test 평가 (한 번만)**. Validation 근거로 Final 을 확정하고 선택 이유를 기록한 뒤에만 실행된다 (가이드 21장, 산출물 5).

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/16_evaluate_final_test.py)

## 사용법

```bash
cd subject8
python scripts/16_evaluate_final_test.py
```

실행 전 조건 (하나라도 없으면 멈춤):
1. `models/final/final_best.pt` 와 [`src/registry.py`](../src/registry.md) 의 `OFFICIAL["final"]` (실행 이름)
2. `reports/final_model_selection.md` (Validation 결과 · 선택 이유 · 원본 Weight)
3. `reports/05_final/final_metrics.csv` 가 아직 없음 (두 번 평가 방지)

| 입력 | 출력 |
|---|---|
| Final Weight, 그 Version 의 Frozen Test (82장) | `reports/05_final/final_metrics.csv` · `final_class_metrics.csv`, `reports/figures/final/final_test_{confusion_matrix, confusion_matrix_normalized, pr_curve}.png`, `runs/eval/final_test_<실행>/` |

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md) (`resolve("final")`), [`src/evaluate_detector`](../src/evaluate_detector.md) (`allow_test=True`), [`src/split_builder`](../src/split_builder.md)
- **사용하는 곳**: 직접 실행 (8일차)

## 주의사항

- 결과는 보고만 한다. Test 점수를 보고 모델·조건을 다시 고르지 않는다 (가이드 4037행).
- 학습 때 imgsz·batch 로 평가한다 (`runs/<실행>/args.yaml`).
