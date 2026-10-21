# `subject8/scripts/17_evaluate_bridge.py`

> 교과 14 용 — Final Model 을 **Bridge Holdout 156장에서 처음 한 번** 평가한다. **교과 8 에서는 실행하지 않는다** (Bridge 는 학습·튜닝·모델 선택·Frozen Test 에 쓰지 않고 보존한 데이터).

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/17_evaluate_bridge.py)

## 사용법

```bash
cd subject8
python scripts/17_evaluate_bridge.py --dry-run       # 확인만: Manifest 156장 = data/bridge_holdout 사진 · 라벨 개수 (모델·사진 내용을 쓰지 않음)
python scripts/17_evaluate_bridge.py --subject14     # 교과 14 에서 처음 한 번 평가
```

| 옵션 | 뜻 |
|---|---|
| `--subject14` | "교과 14 에서 Bridge 를 처음 평가한다"는 확인. **없으면 평가하지 않고 멈춘다** |
| `--dry-run` | `manifests/bridge_holdout.csv` 와 `data/bridge_holdout/` 이 같은지(사진·라벨 개수와 이름)만 확인 |
| `--model` | 기본 `final` (`models/final/final_best.pt`). 실행 이름이나 `.pt` 경로도 가능 |

실행 전 조건 (하나라도 어긋나면 멈춤):
1. `--subject14` 를 붙였다 (실수로 교과 8 에서 돌리는 것을 막는다)
2. `data/bridge_holdout/` 이 Manifest 와 같다 (없거나 다르면 `python scripts/00_setup.py` 로 다시 만든다 — 사진이 있는 PC 에서만 가능)
3. `reports/06_subject14/bridge_metrics.csv` 가 아직 없다 (두 번 평가 방지 — Frozen Test 와 같은 규칙)

| 입력 | 출력 |
|---|---|
| Final Weight, `data/bridge_holdout/{images,labels}` (156장) | `reports/06_subject14/bridge_metrics.csv` · `bridge_class_metrics.csv`, `reports/figures/subject14/bridge_{confusion_matrix, confusion_matrix_normalized, pr_curve}.png`, `runs/eval/bridge_<실행>/` |

평가용 `configs/dataset_bridge.yaml` 은 실행할 때만 만들고 Git 에 올리지 않는다 (`configs/dataset.yaml` 에는 Bridge 를 넣지 않는다).

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/evaluate_detector`](../src/evaluate_detector.md), [`src/split_builder`](../src/split_builder.md), [`src/constants`](../src/constants.md)
- **사용하는 곳**: 직접 실행 (교과 14 첫 단계). 근거 문서: [`docs/project/handoff/subject14_handoff.md`](../project/handoff/subject14_handoff.md) 3·8장

## 주의사항

- 이 점수를 보고 모델·조건을 다시 고르지 않는다. 다시 고를 일이 있으면 교과 14 안의 새 Validation 으로 한다 (그러지 않으면 Bridge 가 Validation 이 된다).
- 학습 때 imgsz·batch 로 평가한다 (`runs/<실행>/args.yaml`). conf 는 Ultralytics 평가 기본값(mAP 계산용)이고, 사진 예측 기준(`--conf 0.25`)과는 다르다.
- Bridge 에는 갈변이 16박스뿐이라 갈변 Recall 은 박스 1개에 6%p 움직인다.
- 교과 8 이 끝난 시점에 이 스크립트로 만든 결과(`reports/06_subject14/`, `runs/eval/bridge_*`)가 없어야 "Bridge 를 쓰지 않았다"가 성립한다. `scripts/qa_acceptance_check.py` 가 이를 점검한다.
