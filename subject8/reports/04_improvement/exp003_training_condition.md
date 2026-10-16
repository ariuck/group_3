# 개선 실험 exp003 학습 조건 (`exp003_v4_imgsz1920_epoch100`)

> 자동 생성: `train_detector.py` · 2026-10-14 16:58

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v4` |
| Train / Val Manifest | `manifests/train.csv` 526장 (sha256 169e6cfcb1f7) / `manifests/val.csv` 132장 (sha256 20c40a376464) |
| Data 설정 | `configs/dataset.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 100 |
| Batch | 6 |
| Image Size | 1920 |
| Seed | 42 (deterministic=True) |
| Optimizer | AdamW |
| Learning Rate (lr0) | 0.001 |
| Augmentation | Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등) |

## 실행 환경

| 항목 | 값 |
|---|---|
| GPU | NVIDIA GeForce RTX 3060 (device 0) |
| GPU 최대 사용 메모리 | 7.6 GB |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-14 16:15:34 |
| 학습 종료 | 2026-10-14 16:58:47 |
| 걸린 시간 | 43분 12초 |
| 실행 폴더 | `runs/exp003_v4_imgsz1920_epoch100` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/exp003_v4_imgsz1920_epoch100/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/exp003_v4_imgsz1920_epoch100/weights/last.pt` |
| results.csv 생성 | ✅ | 100 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/improved/exp003_best.pt` (sha256 017e3ec793ca) |

## 메모

- Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 data/yolo/train·val 이 manifest 와 정확히 같은지 확인했다.
- kimchi_v4 (kimchi_v3 라벨 + G09 마지막 배치 25장 Val — Val 갈변 8 → 75개)로 학습했다. Baseline(06) 조건에서 imgsz 640 → 1920, batch 16 → 6, epochs 50 → 100 으로 바꿨다. 비교 대상: exp002 (epochs 50). 다른 Dataset Version 과는 Val 구성 또는 라벨이 달라 Validation 점수를 직접 비교하지 않는다.
- 근거: 6일차 H4(작은 이물 FN) · kimchi_v1 예비 실험 pilot_v1_imgsz1280 (mAP50-95 0.351 → 0.519) · exp001(640 → 1280, mAP50-95 0.538 → 0.712) · exp002(1280 → 1920, 0.712 → 0.757, best epoch 50).
- exp002 와 다른 변수는 epochs(50 → 100) 하나다. 학습률은 100 epoch 에 맞춰 줄고, mosaic 을 끄는 마무리 10 epoch 는 91~100 으로 옮겨간다.
- 참고 — best.pt 가 저장된 epoch 77 의 학습 중 Validation: P 0.929 · R 0.816 · mAP50 0.913 · mAP50-95 0.774
