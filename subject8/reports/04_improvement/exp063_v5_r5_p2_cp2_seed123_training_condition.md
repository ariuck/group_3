# kimchi_v5 5라운드 exp063 (P2 + 변형 반점 합성) 학습 조건 (`exp063_v5_r5_p2_cp2_seed123`)

> 자동 생성: `train_detector.py` · 2026-10-20 12:23

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11s-p2 (`configs/yolo11s-p2.yaml`, COCO `yolo11s.pt` 에서 맞는 층만 이어받음) |
| Dataset Version | `kimchi_v5` |
| Train / Val Manifest | `manifests/train.csv` 558장 (sha256 989eebc34e7e) / `manifests/val.csv` 104장 (sha256 c897b139828f) |
| Data 설정 | `configs/dataset.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 50 |
| Batch | 1 |
| Image Size | 2240 |
| Seed | 123 (deterministic=True) |
| Optimizer | AdamW |
| Learning Rate (lr0) | 0.001 |
| Augmentation | 기본 + 상하반전 flipud 0.5 (기본 0) · 밝기 hsv_v 0.6 (기본 0.4) — exp007 과 같음 |

## 실행 환경

| 항목 | 값 |
|---|---|
| PC (host) | DESKTOP-761SQI1 |
| OS | Ubuntu 26.04.1 LTS (kernel 6.18.54.1-microsoft-standard-WSL2) |
| CPU / RAM | 12th Gen Intel(R) Core(TM) i7-12700 / 15 GB |
| GPU | NVIDIA GeForce RTX 3060 (device 0, 드라이버 610.88) |
| GPU 최대 사용 메모리 | 5.2 GB |
| Python | 3.14.4 |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-20 10:12:27 |
| 학습 종료 | 2026-10-20 12:23:41 |
| 걸린 시간 | 131분 13초 |
| 실행 폴더 | `runs/exp063_v5_r5_p2_cp2_seed123` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/exp063_v5_r5_p2_cp2_seed123/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/exp063_v5_r5_p2_cp2_seed123/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/improved/exp063_v5_r5_p2_cp2_seed123.pt` (sha256 403cebce8ab3) |

## 메모

- Frozen Test 와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 `data/yolo/train·val` 이 manifest 와 정확히 같은지 확인했다.
- kimchi_v5 = C안 재분할(묶음 통째 배정, 예외는 G00 하나) + 라벨 수정본 kimchi_v5(v3 + 이물 없는 박스 3개 삭제). 기준: `docs/project/kimchi_v5_split.md`. v4 와는 Val 이 달라 점수를 직접 비교하지 않는다.
- Baseline(06) 조건에서 model_name yolo11n.pt → /home/user1/group_3/subject8/configs/yolo11s-p2.yaml, imgsz 640 → 2240, batch 16 → 1, flipud 0.0 → 0.5, hsv_v 0.4 → 0.6, transfer None → yolo11s.pt, seed 42 → 123 으로 바꿨다. 비교 대상: exp018_v5 (B · 같은 seed 123) · B seed 5개 평균 0.739 · 갈변 0.108.
- 5라운드(갈변 진단) 'P2 + 변형 반점 합성' 의 seed 123. Final(exp050) 확정 뒤의 진단 실험이라 Final 을 바꾸지 않는다. 클래스별 갈변 mAP 로 본다.
- 변형 반점 합성 사진 150장을 Train 에 추가: 긴 변 200px 미만 Train 갈변(반점 + 중간 갈변)을 긴 변 18~45px 로 줄여, 하나씩 회전 · 찌그러뜨림 · 색 · 번짐을 바꾸고 반점 픽셀(둘레보다 어두운 곳)만 갈변 없는 Train 사진의 배추 위에 3개씩 붙임 (seed 0, `data/yolo_v5_r4/synth2`, Git 제외). Val 은 원본 그대로.
- 모델 구조: `configs/yolo11s-p2.yaml` (YOLO11s + P2 검출층). COCO `yolo11s.pt` 에서 이름 · 모양이 같은 층만 이어받음 (backbone 전체 + head 앞부분, P2 갈래와 Detect 는 새로 학습).
- 참고 — best.pt 가 저장된 epoch 49 의 학습 중 Validation: P 0.812 · R 0.831 · mAP50 0.870 · mAP50-95 0.725
