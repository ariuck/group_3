# `subject8/scripts/15_eval_inference_options.py`

> 추론 설정 비교 (재학습 없음) — 학습된 모델을 Validation 에서 추론 옵션만 바꿔 평가한다: 기본 · TTA(`augment=True`) · `agnostic_nms` · 둘 다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/15_eval_inference_options.py)

## 사용법

```bash
cd subject8
python scripts/15_eval_inference_options.py                                   # 기본 후보 exp007 · exp008
python scripts/15_eval_inference_options.py --models exp015_v5_s_imgsz2240_aug
```

| 입력 | 출력 |
|---|---|
| 모델 (`models/` — [`registry`](../src/registry.md)), 그 Version 의 Validation | `reports/04_improvement/inference_options.csv` (모델 × 옵션 × 전체·Class 별 P·R·mAP50·mAP50-95 · ms/장), `runs/eval/infer_<실행>_<옵션>/` |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `OPTIONS` | `기본` · `TTA` (좌우반전·크기 바꿔 여러 번 예측해 합침) · `agnostic_nms` (Class 가 달라도 겹친 박스 하나로) · `TTA+agnostic_nms` |
| `main()` | 모델마다 학습 때 imgsz·batch 로 [`evaluate_detector`](../src/evaluate_detector.md)(`**val_kwargs`) 4번 → CSV (같은 모델 줄만 바꿈) |

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/evaluate_detector`](../src/evaluate_detector.md), [`src/split_builder`](../src/split_builder.md)
- **사용하는 곳**: 직접 실행 (Final Model 확정 전 추론 설정 결정)

## 주의사항

- Frozen Test 는 쓰지 않는다. 타일링 모델은 건너뛴다.
- TTA 는 예측이 약 2~3배 느리다 (`ms_per_image`). 채택은 mAP50-95 +0.01 이상이고 속도가 감당될 때만.
- 가설: kimchi_v1 실패 분석 H3 "같은 물체를 두 Class 로 예측" → `agnostic_nms`.
