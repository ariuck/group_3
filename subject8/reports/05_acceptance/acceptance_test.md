# Acceptance Test (교과 8) — 작성 중

> 산출물 7 · 가이드 22.7. 담당: 5번(QA·시연 검증).
> **현재 상태**: 7일차 시점의 자동 점검 결과다. Final Model·Frozen Test·Auto Label(8일차) 항목은 `TODO`, 사진·GPU 가 필요한 항목은 `MANUAL` 로 남아 있고 8~9일차 이후 채운다.

| | |
|---|---|
| 시험 일시 | 2026-10-15 |
| 시험 환경 | WSL Ubuntu · Python 3.14.4 · **사진 없음 · ultralytics/torch/opencv 미설치인 PC** |
| 시험 방법 | `python scripts/qa_acceptance_check.py` (자동 점검) + 사람이 확인하는 항목 |
| 근거 파일 | [`acceptance_check.csv`](acceptance_check.csv) (자동 점검 결과 원본) |
| 다시 실행 | `cd subject8 && python scripts/qa_acceptance_check.py` |

## 결과 요약

| PASS | FAIL | TODO | MANUAL |
|---:|---:|---:|---:|
| 24 | 1 | 7 | 4 |

- **PASS**: 확인 완료 · **FAIL**: 고쳐야 함 · **TODO**: 아직 만들어지지 않은 산출물 · **MANUAL**: 사람이 사진·GPU 가 있는 PC 에서 확인

## 1. Dataset

| 항목 | 결과 | 근거 |
|---|:---:|---|
| 교과 7 FINAL 출처를 추적할 수 있다 (`source_dataset · original_split · scene_type`) | PASS | split_manifest 900장 모두 `출처 데이터셋`·`원래 split`·`이미지 유형`·`capture_group` 기록 |
| Dataset Version 을 확인할 수 있다 | PASS | manifest·dataset_summary 모두 `kimchi_v4` |
| 네 역할 Manifest 가 있고 합이 900장 | PASS | Train 526 · Val 132 · Test 84 · Bridge 158 = 900 |
| `dataset_summary.csv` 가 Manifest 와 같다 | PASS | 네 역할 수량 일치 |
| 역할 사이에 같은 이미지가 없다 | PASS | 겹침 0장 |
| 같은 촬영 묶음이 여러 역할에 섞이지 않았다 | PASS (예외) | **G00·G09·G12 는 섞임** — 의도한 분할 예외이며 `docs/split_policy.md` 에 기록됨. 가이드 Gate 와는 다르므로 예외로 설명해야 한다 |
| Split 정책이 문서로 확정(FROZEN)되어 있다 | PASS | `docs/split_policy.md` |
| Class ID 0~6 을 그대로 쓴다 | PASS | `configs/dataset.yaml` |
| Bridge Holdout 이 `dataset.yaml` 에 없다 | PASS | |
| Frozen Test 가 Final Model 선택 전에 사용되지 않았다 | PASS (휴리스틱) | `runs/` 에 test·final 실행 없음, `evaluate_detector.py` 에 `allow_test` 보호. **학습 로그로 사람이 한 번 더 확인** |
| 학습에 쓴 Train/Val Manifest 가 지금과 같다 | PASS | 해시 일치 (train `169e6cfcb1f7`, val `20c40a376464`) |

## 2. Model

| 항목 | 결과 | 근거 |
|---|:---:|---|
| Baseline · exp001~003 Weight 가 있고 기록과 같다 | PASS | `models/` 의 SHA-256 앞 12자리가 각 `*_training_condition.md` 기록과 일치 |
| Baseline 학습조건이 기록되어 있다 | PASS | `baseline_training_condition.md` |
| `final_best.pt` 가 있다 | TODO | 8일차 Final Model 확정 후 (`models/final/`) |
| Final Model 선택 이유가 기록되어 있다 | TODO | `reports/final_model_selection.md` (8일차). 후보 제안은 `baseline_vs_improved.md` 6장 |

## 3. Evaluation

| 항목 | 결과 | 근거 |
|---|:---:|---|
| Baseline Validation 의 Precision·Recall·mAP50·mAP50-95 | PASS | `baseline_metrics.csv` |
| Class 별 성능 | PASS | `baseline_class_metrics.csv` |
| Failure Analysis | PASS | `failure_analysis.csv` · `failure_hypothesis.md` |
| Baseline vs Improved 비교 | PASS | `baseline_vs_improved.md` |
| 실험 기록 | PASS | `experiment_log.csv` (권장 필드 15개) |
| Frozen Test 결과 | TODO | `reports/final_metrics.csv` (8일차, Final Model 확정 후 한 번만) |

## 4. Inference · Auto Label

| 항목 | 결과 | 확인 방법 |
|---|:---:|---|
| 이미지 Detection 이 실행되고 BBox·Class·Confidence 가 표시된다 | MANUAL | 사진 PC 에서 `python scripts/08_predict_images.py --limit 5` → `runs/predict/baseline_val_images/compare/*.jpg` 확인 |
| 새 이미지에서 YOLO TXT 후보가 저장된다 | TODO | Auto Label 코드 아직 없음 (`src/auto_labeler.py`, `scripts/12_auto_label.py`) |
| 후보 TXT 를 교과 7 라벨링 도구에서 열고 수정·승인·저장할 수 있다 | MANUAL | `cd subject7 && python main.py` → 후보 TXT 폴더 열기 (Auto Label 구현 후) |
| 시연 백업자료 (`demo/prediction_images`, `candidate_labels`, `reviewed_labels`) | TODO | 현재 세 폴더 모두 비어 있음 |

## 5. 환경 · 코드 · 보안

| 항목 | 결과 | 근거 |
|---|:---:|---|
| `src/`·`scripts/` Python 파일이 문법 오류 없이 컴파일된다 | PASS | 전부 정상 |
| 회사 사진이 Git 에 추적되지 않는다 | PASS | 추적 사진 0장 |
| `.pt` 는 `models/` 안의 것만 추적된다 | PASS | |
| 학습·추론 패키지가 설치되어 있다 | **FAIL** | 이 PC 에 `ultralytics`, `torch`, `cv2` 없음 (아래 FAIL 기록) |
| 다른 팀원이 README 만 보고 처음부터 재실행할 수 있다 | MANUAL | README 6장 순서대로 다른 PC 에서 실행 (가이드 22.6) |

## FAIL 기록과 재시험

| # | 항목 | 원인 | 조치 | 재시험 |
|---|---|---|---|---|
| F-1 | 학습·추론 패키지 | 이 PC 의 공용 `.venv` 에는 `pandas`·`matplotlib` 만 있다. 학습·예측용 `ultralytics`·`torch`·`cv2` 는 설치하지 않았다 (이 PC 에는 사진이 없어 학습·예측을 하지 않음) | 사진이 있는 PC 에서 `pip install -r requirements.txt` | **미실시** — 사진 PC 에서 `qa_acceptance_check.py` 를 다시 돌려 PASS 확인 |

## 사람이 확인할 시험 절차 (MANUAL)

사진·GPU 가 있는 PC 에서 하고, 결과는 위 표의 `MANUAL` 칸과 아래에 기록한다.

1. **환경**: `python scripts/01_check_environment.py` → Python·PyTorch·Ultralytics·GPU·`yolo11n.pt` Load 성공
2. **Detection**: `python scripts/08_predict_images.py --limit 5` → 비교 이미지에서 BBox·Class·Confidence 가 보이는가
3. **Frozen Test 미사용 확인**: 학습 로그(`runs/*/args.yaml`)에 `split: test` 가 없는가
4. **재현**: 만든 사람이 아닌 팀원이 README 6장만 보고 환경 → Dataset 경로 → 예측까지 실행. 막힌 곳은 아래에 적는다

| 시험자 | 일시 | 막힌 곳 · 문서와 실제가 다른 곳 | 수정 후 재시험 |
|---|---|---|---|
| | | | |

## 8~9일차에 채울 것

- [ ] Final Model 확정 → `final_best.pt`, `final_model_selection.md`
- [ ] Frozen Test 1회 평가 → `final_metrics.csv`
- [ ] Auto Label 구현 → 후보 TXT → 교과 7 도구에서 열기·수정·승인
- [ ] `demo/` 백업자료 채우기 (사진은 Git 제외)
- [ ] 위 표 `TODO`·`MANUAL` 을 PASS/FAIL 로 바꾸고 FAIL 은 재시험 결과까지 기록
