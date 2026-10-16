# kimchi_v5 개선 실험 exp004 학습 조건 (`exp004_v5_tile2x2`)

> 자동 생성: `train_detector.py` · 2026-10-16 13:05

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v5` 2×2 조각 |
| Train / Val | 조각 2232개 / 416개 (원본 558 / 104장 × 4) |
| Data 설정 | `configs/dataset_v5_tiles.yaml` |
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
| PC (host) | DESKTOP-MGOK18H |
| OS | Ubuntu 26.04.1 LTS (kernel 6.18.54.1-microsoft-standard-WSL2) |
| CPU / RAM | 12th Gen Intel(R) Core(TM) i7-12700 / 15 GB |
| GPU | NVIDIA GeForce RTX 3060 (device 0, 드라이버 610.88) |
| GPU 최대 사용 메모리 | 7.6 GB |
| Python | 3.14.4 |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-16 11:36:40 |
| 학습 종료 | 2026-10-16 13:05:13 |
| 걸린 시간 | 88분 33초 |
| 실행 폴더 | `runs/exp004_v5_tile2x2` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/exp004_v5_tile2x2/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/exp004_v5_tile2x2/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/improved/exp004_v5_tile2x2.pt` (sha256 20d5d81cc2f5) |

## 메모

- Frozen Test 와 Bridge Holdout 은 조각을 만들지 않았고 학습·검증에 쓰지 않았다.
- exp002_v5 (imgsz 1920 · batch 6) 와 다른 변수는 입력 하나: 원본 사진 → 2×2 조각(20% 겹침, 조각 2693×1502). 조각 밖으로 40% 넘게 잘린 박스는 그 조각에서 뺐다.
- 학습 중 Validation(아래 참고값)은 조각 단위라 다른 실험과 비교하지 않는다. 비교는 원본 Val 104장을 조각 예측 합침으로 채점한 `reports/04_improvement/tiling_eval.csv` (src/tiling.evaluate_full).
- 참고 — 조각 Validation best epoch 42: P 0.896 · R 0.794 · mAP50 0.821 · mAP50-95 0.709
