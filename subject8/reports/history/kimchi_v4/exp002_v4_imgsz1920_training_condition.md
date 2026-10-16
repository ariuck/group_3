# 개선 실험 exp002 학습 조건 (`exp002_v4_imgsz1920`)

> 자동 생성: `train_detector.py` · 2026-10-14 14:58

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v4` |
| Train / Val Manifest | `manifests/kimchi_v4/train.csv` 526장 (sha256 169e6cfcb1f7) / `manifests/kimchi_v4/val.csv` 132장 (sha256 20c40a376464) |
| Data 설정 | `configs/dataset_v4.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 50 |
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
| 학습 시작 | 2026-10-14 14:35:57 |
| 학습 종료 | 2026-10-14 14:58:11 |
| 걸린 시간 | 22분 14초 |
| 실행 폴더 | `runs/exp002_v4_imgsz1920` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/exp002_v4_imgsz1920/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/exp002_v4_imgsz1920/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/history/kimchi_v4/exp002_v4_imgsz1920.pt` (sha256 4f2f8d8457a7) |

## 메모

- Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 data/yolo_v4/train·val 이 manifest 와 정확히 같은지 확인했다.
- kimchi_v4 (kimchi_v3 라벨 + G09 마지막 배치 25장 Val — Val 갈변 8 → 75개)로 학습했다. Baseline(06) 조건에서 imgsz 640 → 1920, batch 16 → 6 으로 바꿨다. 비교 대상: exp001 (imgsz 1280). 다른 Dataset Version 과는 Val 구성 또는 라벨이 달라 Validation 점수를 직접 비교하지 않는다.
- 근거: 6일차 H4(작은 이물 FN) · kimchi_v1 예비 실험 pilot_v1_imgsz1280 (mAP50-95 0.351 → 0.519) · exp001(640 → 1280, mAP50-95 0.538 → 0.712).
- batch 16 → 6 은 GPU 메모리 때문이다 (batch 8 은 12.9GB 로 12GB 초과). nbs=64 gradient 누적으로 갱신 1번당 사진 수는 exp001 64장 · exp002 66장으로 거의 같다.
- 참고 — best.pt 가 저장된 epoch 50 의 학습 중 Validation: P 0.944 · R 0.816 · mAP50 0.891 · mAP50-95 0.757
