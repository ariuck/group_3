# Acceptance Test (교과 8) — Final Model · Frozen Test 반영판

> 산출물 7 · 가이드 22.7. 담당: 5번(QA·시연 검증).
> **현재 상태**: Final Model(`exp050`)과 Frozen Test 까지 확인했다. 남은 것은 **Auto Label(8일차 구현)과 그 시연 백업자료**이며 (v5 실패 원인 가설 문서는 `03_failure_analysis/failure_hypothesis.md` 로 작성됨) `TODO` 로 표시했다. 사람이 해야 하는 `MANUAL` 중 이 PC 에서 가능한 것은 직접 확인해 아래에 기록했다.

| | |
|---|---|
| 시험 일시 | 2026-10-20 |
| 시험 환경 | WSL Ubuntu · Python 3.14.4 · PyTorch 2.14.1+cu130 · Ultralytics 8.4.175 · **RTX 3060 · 사진 있음** |
| 시험 대상 | Dataset `kimchi_v5` · Final Model `exp050_v5_s_imgsz2240_aug_seed2` (`models/final/final_best.pt`) |
| 시험 방법 | `python scripts/qa_acceptance_check.py` (자동 점검) + 사람이 확인하는 항목 |
| 근거 파일 | [`acceptance_check.csv`](acceptance_check.csv) (자동 점검 결과 원본) |
| 다시 실행 | `cd subject8 && python scripts/qa_acceptance_check.py` |

이전판(2026-10-15)은 `kimchi_v4` 기준 · 사진 없는 PC 에서 낸 결과였다 (PASS 24 · FAIL 1 · TODO 7 · MANUAL 4). 그 뒤 Dataset 이 `kimchi_v5` 로 바뀌고 Final · Frozen Test 가 확정되어 다시 시험했다.

## 결과 요약

| | PASS | FAIL | TODO | MANUAL |
|---|---:|---:|---:|---:|
| 자동 점검 (2026-10-20 오후, exp026 · 027 · 063 Weight 추가 후 재실행) | 83 | **0** | 4 | 4 |
| 사람이 확인해 PASS 로 바꾼 것 | +2 | | | −2 |
| **최종** | **85** | **0** | **4** | **2** |

- **PASS**: 확인 완료 · **FAIL**: 고쳐야 함 · **TODO**: 아직 만들어지지 않은 산출물 · **MANUAL**: 사람이 직접 확인해야 함
- 이전판 FAIL(F-1, 학습·추론 패키지)은 사진·GPU PC 에서 다시 시험해 **해결**됐다 (아래 FAIL 기록).
- 자동 점검 83 중 Model 의 Weight 해시 일치가 53개다 (Baseline · exp001~050 · exp063 — 10-20 오후 exp026 · 027 · 063 추가).

## 1. Dataset

| 항목 | 결과 | 근거 |
|---|:---:|---|
| 교과 7 FINAL 출처를 추적할 수 있다 (`source_dataset · original_split · scene_type`) | PASS | split_manifest 900장 모두 기록 |
| Dataset Version 을 확인할 수 있다 | PASS | manifest · dataset_summary 모두 `kimchi_v5` |
| 네 역할 Manifest 가 있고 합이 900장 | PASS | Train 558 · Val 104 · Test 82 · Bridge 156 = 900 |
| `dataset_summary.csv` 가 Manifest 와 같다 | PASS | 네 역할 수량 일치 |
| 역할 사이에 같은 이미지가 없다 | PASS | 겹침 0장 |
| 같은 촬영 묶음이 여러 역할에 섞이지 않았다 | PASS (예외) | 섞인 묶음은 **G00 하나** (v4 는 3개였음). 파·고추(Class 6) 50장이 몰려 있어 시간순 블록으로 나눈 **의도한 예외**이며 `docs/project/split_policy.md` 21~22행에 기록됨 (사람이 확인함). 가이드 Gate 와는 다르므로 발표에서 예외로 설명해야 한다 |
| Split 정책이 문서로 확정(FROZEN)되어 있다 | PASS | `docs/project/split_policy.md` |
| Class ID 0~6 을 그대로 쓴다 | PASS | `configs/dataset.yaml` |
| Bridge Holdout 이 `dataset.yaml` 에 없다 | PASS | |
| Frozen Test 가 Final Model 선택 전에 사용되지 않았다 | **PASS (예외 1건 기록)** | `runs/` 에 test·final 이름의 실행 없음 · `runs/*/args.yaml` 에 `split: test` 0개 · `evaluate_detector.py` 의 `allow_test` 보호. **그러나 팀 기록(`04_improvement/baseline_vs_improved.md` 3장)에 "2026-10-16 Final 확정 전에 Test 점수를 한 번 본 적이 있다 (결과·스크립트는 지움)"고 적혀 있다.** 그 점수로 모델·조건을 고르지 않았다고 하나, 자동 점검은 남은 기록만 보므로 이 열람을 잡지 못한다. 가이드 Gate("Frozen Test 를 보고 Fine-tuning 하지 않는다")와의 관계는 **발표에서 사실대로 설명**해야 한다 |
| Bridge Holdout 을 교과 8 에서 사용하지 않았다 | PASS (휴리스틱) | `runs/` · `runs/eval` · `reports/06_subject14` 에 Bridge 사용 흔적 없음 · `configs/dataset.yaml` 에 Bridge 없음 · Bridge 평가 스크립트(`17_evaluate_bridge.py`)는 `--subject14` 없이는 멈추고 교과 8 에서 실행하지 않았다. 한계: 남은 기록만 보는 점검 |
| 학습에 쓴 Train/Val Manifest 가 지금과 같다 | PASS | 해시 일치 |

## 2. Model

| 항목 | 결과 | 근거 |
|---|:---:|---|
| Baseline · exp001~050 · exp063 Weight 가 있고 기록과 같다 | PASS | `models/` 의 SHA-256 앞 12자리가 각 `*_training_condition.md` 와 일치 (53개 모두) |
| Baseline 학습조건이 기록되어 있다 | PASS | `reports/02_baseline/baseline_training_condition.md` |
| `final_best.pt` 가 있다 | PASS | `models/final/final_best.pt` |
| Final Model 선택 이유가 기록되어 있다 | PASS | `reports/final_model_selection.md` (후보 A·B·C seed 평균, 4라운드 6방향) |
| `final_best.pt` 가 공식 Final 실행의 Weight 이고 선택 문서의 해시와 같다 | PASS | `exp050_v5_s_imgsz2240_aug_seed2` · sha256 `a185c4401ace…` — `models/improved/` 원본 · 선택 문서 · `src/registry.py` 모두 일치 |

## 3. Evaluation

| 항목 | 결과 | 근거 |
|---|:---:|---|
| Baseline Validation 의 Precision·Recall·mAP50·mAP50-95 | PASS | `02_baseline/baseline_metrics.csv` (mAP50-95 0.471 — `07` 재평가. 실험 비교표의 0.470 은 학습 중 best epoch 값) |
| Class 별 성능 | PASS | `baseline_class_metrics.csv` (Class 4 는 Instance 0건으로 표시) |
| Failure Analysis 표 | PASS | `03_failure_analysis/failure_analysis.csv` 외 3개 |
| 실패 원인 가설 문서 | PASS | `03_failure_analysis/failure_hypothesis.md` — v5 기준 H1~H5 와 이후 검증 (2026-10-20 작성). 사진을 봐야 아는 부분(FP_BACKGROUND 24건에 빠진 라벨이 있는지 등)은 문서 안에 「사람 확인 필요」로 남아 있다 |
| 개선 실험 설계 문서 | PASS | `04_improvement/improvement_experiment.md` |
| 실험 기록 완전성 | PASS (보완함) | `experiment_log.csv` 에 exp009 · 011 · 014~050 행이 빠져 있었다 (13행). 자동 점검은 열 이름만 봐서 통과했었다. 2026-10-20 에 39행을 덧붙여 52행, 같은 날 오후 exp063 을 더해 **53행**. 점수 없는 실행은 exp017(중단) 하나 — exp026 · 027 은 재학습 결과로 채웠다 |
| Baseline vs Improved 비교 | PASS | `04_improvement/baseline_vs_improved.md` |
| 실험 기록 | PASS | `experiment_log.csv` (권장 필드 15개) |
| Frozen Test 결과 (Final 1개 · 한 번 · 82장) | PASS | `05_final/final_metrics.csv` — 1행, `exp050`, 82장 · 432박스, **mAP50-95 0.639** · mAP50 0.726 · P 0.868 · R 0.744 |
| Frozen Test 를 잰 모델이 공식 Final 과 같다 | PASS | 같은 실행 이름 |
| Frozen Test Class 별 성능 | PASS | `05_final/final_class_metrics.csv` |

**해석할 때 주의할 점 (사람이 읽고 적음)**

- Val 0.749 → Test 0.639 로 0.11 낮다. Val 0.749 는 seed 5개 중 최고를 고른 값이라 부풀어 있고 (B 평균 0.739), Test 는 Val 과 다른 촬영 묶음이다. **대외 성능은 Test 0.639 로 말한다.**
- Test 에서 **갈변(Class 5) Recall 0.00 · mAP50-95 0.007**, 나뭇잎·종이(Class 0) Precision 0.37 이다. 평균 점수 뒤에 이 두 Class 가 있으므로 발표·인계 문서에서 같이 말해야 한다 ([`docs/project/handoff/subject14_handoff.md`](../../docs/project/handoff/subject14_handoff.md) 5장).
- Class 5 · 3 은 박스가 16 · 23개뿐이라 박스 1개로 점수가 크게 움직인다.

## 4. Inference · Auto Label

| 항목 | 결과 | 확인 방법 · 근거 |
|---|:---:|---|
| 이미지 Detection 이 실행되고 BBox·Class·Confidence 가 표시된다 | PASS (사람이 확인) | `python scripts/08_predict_images.py --model final --name final_val_all` → **Val 104장 전체** · 예측 538 · 정답 541 · TP 506 · Class 틀림 1 · FP 31 · FN 34 (2026-10-20). `runs/predict/final_val_all/compare/*.jpg` 에서 Class 별 대표 사진을 눈으로 확인함: 나뭇잎·종이(5/5, conf 0.74~0.98) · 플라스틱 · 나뭇가지(0.86) · 벌레(0.87) · 파·고추(0.90~0.93) · 갈변(작은 반점 1개는 0.61 로 찾고 1개는 놓침). 왼쪽 정답 · 오른쪽 예측에 BBox · Class 이름 · Confidence 가 모두 표시된다. 이전판(Val 앞 5장, 모두 Class 6)의 "다른 Class 는 보지 못했다"는 한계는 해소됨. **참고**: 처음 Val 전체를 돌렸을 때 GPU 메모리 초과(imgsz 2240, 사진이 한꺼번에 묶임)가 나서 `08_predict_images.py` · `src/failure_analyzer.py` 를 사진 한 장씩 예측하도록 고쳤다 |
| 새 이미지에서 YOLO TXT 후보가 저장된다 | TODO | Auto Label 코드 아직 없음 (`src/auto_labeler.py`, `scripts/12_auto_label.py`) |
| 후보 TXT 를 교과 7 라벨링 도구에서 열고 수정·삭제·추가·승인·저장할 수 있다 | MANUAL | Auto Label 구현 후 `cd subject7 && python main.py` 로 후보 TXT 폴더를 열어 확인 |
| 시연 백업자료: 예측 이미지 | TODO | `demo/prediction_images/` 비어 있음 (사진이라 Git 제외, 시연 PC 에 둔다) |
| 시연 백업자료: Auto Label 후보 | TODO | `demo/auto_label/candidate_labels/` 비어 있음 |
| 시연 백업자료: 검수 완료 라벨 | TODO | `demo/auto_label/reviewed_labels/` 비어 있음 |

## 5. 환경 · 코드 · 보안

| 항목 | 결과 | 근거 |
|---|:---:|---|
| `src/`·`scripts/` Python 파일이 문법 오류 없이 컴파일된다 | PASS | 전부 정상 |
| 회사 사진이 Git 에 추적되지 않는다 | PASS | 추적 사진 0장. 발표자료는 `subject8/` 밖 저장소 맨 위 `presentation/` 로 옮겼고(2026-10-20) 이 점검이 그 폴더도 본다 — 사진·영상·PDF 는 막고, `presentation/assets/` 의 PNG 7개(혼동행렬·비교 그래프·가짜 샘플 UI 캡처)는 그래프·화면 캡처라 허용한다. 2026-10-20 사람이 `ui_main.png` · `readme_2_RAW비교.png` 를 열어 회사 사진이 아님을 확인함. PNG 로 저장한 실제 사진은 이 점검이 못 잡으므로 사람이 본다 |
| `.pt` 는 `models/` 안의 것만 추적된다 | PASS | |
| 학습·추론 패키지가 설치되어 있다 | PASS | ultralytics · torch · cv2 import 가능, CUDA available True (RTX 3060) |
| 환경 점검 | PASS (사람이 확인) | `01_check_environment.py` — Python 3.14.4 · PyTorch 2.14.1+cu130 · Ultralytics 8.4.175 · GPU · `yolo11n.pt` Load 성공 |
| 교과 14 Handoff 문서가 있다 (Final · Bridge · Version · 한계 포함) | PASS | [`docs/project/handoff/subject14_handoff.md`](../../docs/project/handoff/subject14_handoff.md) |
| 다른 팀원이 README 만 보고 처음부터 재실행할 수 있다 | MANUAL | 아래 재현 시험 표. 2026-10-21 README·실행 가이드·Final·Frozen Test·인계 링크 정리 완료. 다른 팀원의 독립 재현은 아직 확인하지 않았으므로 MANUAL 유지 |

## FAIL 기록과 재시험

| # | 항목 | 원인 | 조치 | 재시험 |
|---|---|---|---|---|
| F-1 | 학습·추론 패키지 | (2026-10-15) 사진 없는 PC 의 공용 `.venv` 에 `ultralytics`·`torch`·`cv2` 가 없었다 | 사진·GPU PC 에서 시험 | **2026-10-20 PASS** — 이 PC 의 `.venv` 에 모두 있고 `qa_acceptance_check.py` 에서 FAIL 0 |

현재 열린 FAIL 은 없다.

## 이번에 바꾼 점검 코드 (`scripts/qa_acceptance_check.py`)

Final · Frozen Test 가 생기면서 점검 기준과 실제 파일 위치가 달라, 점검이 `TODO` 로 남을 뻔한 것을 고쳤다.

- Frozen Test 결과 위치를 `reports/final_metrics.csv` → `reports/05_final/final_metrics.csv` 로 맞춤
- 추가한 점검: ① `final_best.pt` = 공식 Final 실행의 Weight = 선택 문서에 적힌 해시 ② Frozen Test 가 **1행 · Test 82장 · 공식 Final** 로 잰 것인지 ③ Class 별 Test 성능 파일 ④ `docs/project/handoff/subject14_handoff.md` 가 있고 Final · Bridge · Dataset Version · 한계를 다루는지 ⑤ **`models/` 에 보관된 모든 Weight 가 `experiment_log.csv` 에 행이 있는지** (열 이름만 보던 점검이 exp009 · 011 · 014~050 누락을 놓쳤다)

## 사람이 확인할 시험 절차 (MANUAL)

1. ~~환경~~ — 2026-10-20 완료 (위 5장)
2. ~~Detection~~ — 2026-10-20 완료, 단 Class 6 사진 5장뿐 (위 4장). **Class 0~3 · 5 가 들어 있는 사진으로 한 번 더** 보면 좋다 (`--limit` 를 늘리거나 `--source` 로 지정)
3. ~~Frozen Test 미사용 확인~~ — 2026-10-20 완료 (`args.yaml` 에 `split: test` 없음). 단 10-16 에 한 번 본 적이 있다는 팀 기록이 있어 "미사용"은 아니다 (위 1장)
4. **재현**: 만든 사람이 아닌 팀원이 [`docs/project/handoff/subject14_handoff.md`](../../docs/project/handoff/subject14_handoff.md) 7장 순서로 환경 → Dataset 경로 → 예측까지 실행. 막힌 곳은 아래에 적는다
5. **Auto Label → 교과 7 도구**: Auto Label 구현 후 후보 TXT 를 열어 수정·삭제·추가·승인·저장이 되는지 확인

| 시험자 | 일시 | 막힌 곳 · 문서와 실제가 다른 곳 | 수정 후 재시험 |
|---|---|---|---|
| | | | |

## 남은 일 (이 문서를 최종으로 만들려면)

- [ ] Auto Label 구현 → 후보 TXT → 교과 7 도구에서 열기·수정·승인 (4장 TODO 1 · MANUAL 1)
- [ ] `demo/` 백업자료 채우기 (사진은 Git 제외, 시연 PC 에 보관) (4장 TODO 3)
- [x] `failure_hypothesis.md` · `improvement_experiment.md` v5 기준 작성 (2026-10-20)
- [x] `experiment_log.csv` 빠진 행 39개 추가(13 → 52행), `baseline_vs_improved.md` Final 기준 갱신 (2026-10-20)
- [ ] 실패 사진으로 `FP_BACKGROUND` 24건 확인 (빠진 라벨 여부) — `failure_hypothesis.md` H5
- [x] README·상세 실행 가이드·Final·Frozen Test·Detection·Handoff 링크 정리 (2026-10-21, 문서 점검; 모델 평가·인수 시험 전체를 다시 실행한 기록은 아님)
- [ ] 다른 팀원 재현 시험 1회 (위 표)
- [ ] 위가 끝나면 `python scripts/qa_acceptance_check.py` 를 다시 돌려 TODO 가 0 인지 확인하고 이 문서의 결과 요약을 갱신
