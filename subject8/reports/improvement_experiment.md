# 개선 실험 설계 (`exp001`)

> 산출물 · 20.3. 입력: 3일차 Dataset Version(`kimchi_v4`) + 6일차 [`failure_hypothesis.md`](failure_hypothesis.md)
> 숫자 근거: [`runs_summary.csv`](runs_summary.csv), [`exp001_training_condition.md`](exp001_training_condition.md) · 전체 기록: [`experiment_log.csv`](experiment_log.csv)

> **작성 시점 메모**: 이 문서는 exp001 학습(2026-10-14) **이후에** 정리했다. 변경 변수와 이유는 학습 전 `failure_hypothesis.md` 5장(H4 → imgsz)에서 이미 정해져 있었고, 이 문서는 그것을 20.3 형식으로 옮겨 적은 것이다. 아래 "Validation 결과"는 학습 후에 채웠다.

```text
Dataset kimchi_v4  +  failure_hypothesis.md (H4)
        ↓
변경 변수 1개: imgsz 640 → 1280
        ↓
유지할 조건: Model · Dataset · Epoch · Batch · Seed · Optimizer · lr0 · Augmentation
        ↓
확인할 Validation 지표와 실패 패턴
        ↓
reports/improvement_experiment.md
        ↓ (학습)
runs/exp001_v4_imgsz1280/weights/best.pt → models/improved/exp001_best.pt
```

## 1. 무엇을 바꾸는가 (변경 변수 1개)

| 항목 | Baseline (`baseline_v4`) | exp001 |
|---|---|---|
| **Image Size (`imgsz`)** | 640 | **1280** |

- 분류: MODEL/TRAIN (입력 해상도) — `failure_hypothesis.md` **H4**
- 바꾸는 값은 `imgsz` 하나뿐이다.

## 2. 왜 바꾸는가

| 근거 | 내용 |
|---|---|
| 실패 패턴 (H4) | 작은 박스(<150px)의 Recall 이 낮다: 나뭇가지 0.20 · 벌레 0.47 · 플라스틱 0.66 · **갈변 0.00** (중간 박스 150~300px 는 0.75~0.86) |
| 원인 추정 | 원본 4K(4848px) 를 640 으로 줄이면 약 1/7.6. Val 갈변 중앙값 57px → 약 7px, 150px 박스 → 약 20px 로 작아져 특징이 사라진다 |
| 예비 실험 | `pilot_v1_imgsz1280` (kimchi_v1): mAP50-95 0.351 → 0.519 |
| 다른 후보를 고르지 않은 이유 | 모델 크기·Epoch 는 H1·H2 분석에서 "Val 손실이 이미 멈췄고, 본 적 없는 모습은 재학습으로 안 고쳐진다"고 판단해 **바꾸지 않기로** 했다. H3(`agnostic_nms`)는 추론 설정이라 학습 변수가 아니다 |

## 3. 유지할 조건 (Baseline 과 동일해야 한다)

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습) |
| Dataset Version | `kimchi_v4` — Train 526장 / Val 132장 (manifest sha256 `169e6cfcb1f7` / `20c40a376464`) |
| Epoch | 50 |
| Batch | 16 |
| Seed | 42 (deterministic) |
| Optimizer / lr0 | AdamW / 0.001 |
| Augmentation | Ultralytics 기본값 |
| 사용하지 않는 데이터 | Frozen Test · Bridge Holdout (학습·검증에 쓰지 않음) |

## 4. 확인할 Validation 지표와 실패 패턴

비교 대상은 같은 Version·같은 Val 의 `baseline_v4` 이다 (다른 Dataset Version 의 점수는 비교하지 않는다).

| 확인 | 기대 | 판정 기준 |
|---|---|---|
| Validation mAP50-95 | 상승 | Baseline 보다 높고, 한 번의 Seed 우연이 아닐 만큼 차이가 크다 |
| Validation Recall | 상승 | 작은 이물을 더 찾는다는 가설과 일치 |
| Validation Precision | 하락하지 않음 | 크게 떨어지면 FP 가 늘었다는 뜻이므로 기록 |
| 실패 패턴: 작은 박스 FN (H4) | 감소 | 특히 Class 5 갈변, Class 2 나뭇가지, Class 3 벌레의 작은 박스 Recall |
| 실패 패턴: CLASS_ERROR / FP_DUPLICATE (H1·H3) | 변화 없음 예상 | 해상도로는 안 고쳐지는 항목 — 줄지 않아도 가설 실패가 아니다 |
| 부작용 | 기록 | 학습 시간, GPU 메모리 (640: 2.1GB → 1280: 8.4GB 로 증가) |

## 5. Validation 결과 (학습 후 기록)

`runs_summary.csv` 의 best epoch 기준 학습 중 Validation 값.

| | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| `baseline_v4` (imgsz 640) | 0.8365 | 0.6745 | 0.7636 | 0.5344 |
| **`exp001` (imgsz 1280)** | **0.9386** | **0.7820** | **0.8840** | **0.7075** |
| 변화 | +0.102 | +0.108 | +0.120 | **+0.173** |

- 기대한 방향(mAP50-95·Recall 상승, Precision 유지)과 일치한다. best epoch 는 39 / 50.
- 학습 시간 4분 36초 → 10분 16초, GPU 최대 메모리 2.1GB → 8.4GB.
- **아직 확인하지 않은 것**: 위 4장의 "작은 박스 Recall"과 CLASS_ERROR·FP_DUPLICATE 건수를 exp001 Weight 로 다시 집계하는 일 (`scripts/09_collect_failures.py`). 이 결과가 나오기 전까지 "H4 가 맞았다"고 단정하지 않고, "mAP50-95 가 올랐다"까지만 말할 수 있다.
- Frozen Test 는 아직 평가하지 않았다.

## 6. 보관 위치

```text
runs/exp001_v4_imgsz1280/weights/best.pt
        ↓
models/improved/exp001_best.pt   (sha256 a9348f85fd70)
```

> 처음 실행 이름은 `baseline_kimchi_v4` 였고 이후 `exp001_v4_imgsz1280` 으로 정리했다 (`args.yaml` 에는 옛 이름이 남아 있다).

## 7. 이후 실험 (같은 방식, 변수 1개씩)

| 실험 | 변경 변수 | 비교 대상 | 이유 | mAP50-95 |
|---|---|---|---|---:|
| `exp002_v4_imgsz1920` | imgsz 1280 → **1920** | exp001 | 1280 에서도 남은 작은 이물 FN | 0.7075 → 0.7575 |
| `exp003_v4_imgsz1920_epoch100` | epochs 50 → **100** | exp002 | exp002 의 best epoch 가 마지막(50)이라 아직 학습이 덜 끝났을 가능성 | 0.7575 → 0.7742 |

- exp002 는 imgsz 와 함께 **batch 16 → 6** 도 바뀌었다. GPU 12GB 한계(batch 8 = 12.9GB) 때문이다. nbs=64 gradient 누적으로 갱신 1번당 사진 수는 64장 → 66장으로 거의 같지만, 엄밀히는 변수 1개 실험이 아니다.
- 전체 수치와 판정은 [`experiment_log.csv`](experiment_log.csv) 에 있다. 실패했거나 비교할 수 없는 실험도 지우지 않았다.
