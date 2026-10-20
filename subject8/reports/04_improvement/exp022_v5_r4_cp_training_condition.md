# kimchi_v5 4라운드 exp022 (B + 반점 합성) 학습 조건 (`exp022_v5_r4_cp`)

> 자동 생성: `train_detector.py` · 2026-10-19 18:44

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11s (`yolo11s.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v5` |
| Train / Val Manifest | `manifests/train.csv` 558장 (sha256 989eebc34e7e) / `manifests/val.csv` 104장 (sha256 c897b139828f) |
| Data 설정 | `configs/dataset.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 50 |
| Batch | 2 |
| Image Size | 2240 |
| Seed | 42 (deterministic=True) |
| Optimizer | AdamW |
| Learning Rate (lr0) | 0.001 |
| Augmentation | 기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp007 과 같음 |

## 실행 환경

| 항목 | 값 |
|---|---|
| PC (host) | DESKTOP-MGOK18H |
| OS | Ubuntu 26.04.1 LTS (kernel 6.18.54.1-microsoft-standard-WSL2) |
| CPU / RAM | 12th Gen Intel(R) Core(TM) i7-12700 / 15 GB |
| GPU | NVIDIA GeForce RTX 3060 (device 0, 드라이버 610.88) |
| GPU 최대 사용 메모리 | 6.7 GB |
| Python | 3.14.4 |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-19 17:25:40 |
| 학습 종료 | 2026-10-19 18:44:07 |
| 걸린 시간 | 78분 26초 |
| 실행 폴더 | `runs/exp022_v5_r4_cp` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/exp022_v5_r4_cp/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/exp022_v5_r4_cp/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/improved/exp022_v5_r4_cp.pt` (sha256 78d09852dd0a) |

## 메모

- Frozen Test 와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `data/yolo/train·val` 이 manifest 와 정확히 같은지 확인했다.
- kimchi_v5 = C안 재분할(묶음 통째 배정, 예외는 G00 하나) + 라벨 수정본 kimchi_v5(v3 + 이물 없는 박스 3개 삭제). 기준: `docs/project/kimchi_v5_split.md`. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.
- Baseline(06) 조건에서 model_name yolo11n.pt → yolo11s.pt, imgsz 640 → 2240, batch 16 → 2, flipud 0.0 → 0.5, hsv_v 0.4 → 0.6, seed 42 → 42 으로 바꿨다. 비교 대상: exp015_v5 (B · 같은 seed 42) · B seed 3개 평균 0.735.
- 4라운드 방향 'B + 반점 합성' 의 seed 42. 갈변(작은 반점) 개선이 목적이라 클래스별 갈변 mAP 도 함께 본다.
- 반점 합성 사진 150장을 Train 에 추가: 긴 변 100px 미만 갈변 반점을 갈변 없는 Train 사진의 배추 위에 3개씩 붙임 (seed 0, `data/yolo_v5_r4/synth`, Git 제외). Val 은 원본 그대로.
- 참고 — best.pt 가 저장된 epoch 46 의 학습 중 Validation: P 0.923 · R 0.794 · mAP50 0.831 · mAP50-95 0.748
