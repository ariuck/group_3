# kimchi_v5 개선 실험 exp006 학습 조건 (`exp006_v5_imgsz2560_aug`)

> 자동 생성: `train_detector.py` · 2026-10-16 20:39

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v5` |
| Train / Val Manifest | `manifests/train.csv` 558장 (sha256 989eebc34e7e) / `manifests/val.csv` 104장 (sha256 c897b139828f) |
| Data 설정 | `configs/dataset.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 50 |
| Batch | 3 |
| Image Size | 2560 |
| Seed | 42 (deterministic=True) |
| Optimizer | AdamW |
| Learning Rate (lr0) | 0.001 |
| Augmentation | 기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp005 와 같음 |

## 실행 환경

| 항목 | 값 |
|---|---|
| PC (host) | DESKTOP-MGOK18H |
| OS | Ubuntu 26.04.1 LTS (kernel 6.18.54.1-microsoft-standard-WSL2) |
| CPU / RAM | 12th Gen Intel(R) Core(TM) i7-12700 / 15 GB |
| GPU | NVIDIA GeForce RTX 3060 (device 0, 드라이버 610.88) |
| GPU 최대 사용 메모리 | 7.7 GB |
| Python | 3.14.4 |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-16 15:36:08 |
| 학습 종료 | 2026-10-16 20:39:25 |
| 걸린 시간 | 303분 17초 |
| 실행 폴더 | `runs/exp006_v5_imgsz2560_aug` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/exp006_v5_imgsz2560_aug/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/exp006_v5_imgsz2560_aug/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/improved/exp006_v5_imgsz2560_aug.pt` (sha256 8c98b9d7e4b4) |

## 메모

- Frozen Test 와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `data/yolo/train·val` 이 manifest 와 정확히 같은지 확인했다.
- kimchi_v5 = C안 재분할(묶음 통째 배정, 예외는 G00 하나) + 라벨 수정본 kimchi_v5(v3 + 이물 없는 박스 3개 삭제). 기준: `docs/project/kimchi_v5_split.md`. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.
- Baseline(06) 조건에서 imgsz 640 → 2560, batch 16 → 3, flipud 0.0 → 0.5, hsv_v 0.4 → 0.6 으로 바꿨다. 비교 대상: exp005_v5 (imgsz 1920 · 같은 증강) — exp002_v5 대비로는 해상도·증강 두 변수.
- exp005_v5 와 다른 변수는 imgsz(1920 → 2560) 하나 (batch 6 → 3 은 GPU 메모리 때문, nbs=64 gradient 누적으로 갱신 1번당 사진 수는 거의 같음). exp002_v5 대비로는 해상도·증강 두 변수를 함께 바꾼 실험이다.
- 참고 — best.pt 가 저장된 epoch 49 의 학습 중 Validation: P 0.872 · R 0.814 · mAP50 0.832 · mAP50-95 0.722
