# 교과 14 Handoff (교과 8 → 교과 14)

> 교과 8(조각김치 이물검출 Object Detection)의 결과를 교과 14(제조 제품검사)에서 바로 이어 쓸 수 있도록 **무엇이 어디에 있고, 무엇을 지키고, 무엇이 아직 안 되는지** 한곳에 정리한 문서입니다. 산출물 7.
> 숫자는 2026-10-20 기준이며 근거 파일을 함께 적었습니다. 성능 숫자는 이 문서를 고쳐 쓰지 말고 근거 파일에서 다시 읽습니다.
>
> **데이터 성격**: AI캠퍼스 교육을 위해 실제 산업데이터와 유사한 분포 구조로 100% 가상 생성된 조각김치 이물검출 학습데이터를 사용했습니다. 실제 생산라인 원본 데이터라고 표현하지 않습니다.
>
> **보안**: 김치·이물 사진은 Git 에 없습니다 (NDA·기관 보안정책). 라벨·Manifest·Weight·보고서만 Git 에 있습니다.

## 1. 한눈에

| 항목 | 값 | 근거 |
|---|---|---|
| Final Model | `exp050_v5_s_imgsz2240_aug_seed2` (YOLO11s · imgsz 2240) | [`reports/final_model_selection.md`](../../../reports/final_model_selection.md) |
| Weight | `models/final/final_best.pt` (sha256 `a185c4401ace…1845b`) | 같은 문서 · `models/improved/exp050_….pt` 와 동일 |
| Dataset Version | `kimchi_v5` (Train 558 · Val 104 · Frozen Test 82 · Bridge Holdout 156 = 900) | [`reports/01_data/dataset_summary.csv`](../../../reports/01_data/dataset_summary.csv) |
| Validation (Final 선택 근거) | mAP50-95 **0.749** · P 0.945 · R 0.822 | `final_model_selection.md` |
| **Frozen Test (최종 성능)** | mAP50-95 **0.639** · mAP50 0.726 · P 0.868 · R 0.744 (82장 · 432박스) | [`reports/05_final/final_metrics.csv`](../../../reports/05_final/final_metrics.csv) |
| Baseline (비교용) | `baseline_v5` YOLO11n · 640 · Val mAP50-95 0.470 | [`reports/02_baseline/`](../../../reports/02_baseline) |
| 예측 속도 | 약 37ms/장 (RTX 3060 · imgsz 2240 · batch 1) | `final_model_selection.md` |

**교과 14 에서 말할 성능은 Frozen Test 0.639 입니다.** Validation 0.749 는 seed 5개 중 최고를 고른 값이라 조금 부풀어 있습니다 (같은 조건의 seed 5개 평균 0.739). Test 점수를 보고 모델을 다시 고르지 않았습니다. (다만 2026-10-16 Final 확정 전에 Test 점수를 한 번 본 적이 있다는 팀 기록이 있습니다 — [`baseline_vs_improved.md`](../../../reports/04_improvement/baseline_vs_improved.md) 3장. 그 점수로 모델·조건을 고르지는 않았습니다.)

## 2. 어디에 무엇이 있나

| 필요한 것 | 위치 |
|---|---|
| 최종 모델 | `models/final/final_best.pt` — 모든 모델 목록 [`models/README.md`](../../../models/README.md) |
| 모델 이름 → Weight · imgsz 찾기 | `src/registry.py` (`OFFICIAL["final"]`) |
| Class 정의 · Dataset 설정 | `configs/dataset.yaml` (Class ID 0~6, Bridge 는 넣지 않음) |
| 분할 결과 | `manifests/split_manifest.csv` + `train.csv` · `val.csv` · `test.csv` · `bridge_holdout.csv` |
| 분할 정책 | [`split_policy.md`](../split_policy.md) (FROZEN) · [`kimchi_v5_split.md`](../kimchi_v5_split.md) |
| 학습 조건 (실험마다) | `reports/04_improvement/<실행>_training_condition.md` · `experiment_log.csv` |
| 개선점 · 한계 (발표용) | [`reports/04_improvement/baseline_vs_improved.md`](../../../reports/04_improvement/baseline_vs_improved.md) |
| 시연 절차 | [`demo_procedure.md`](../demo_procedure.md) |
| 환경 재현 | `requirements.txt` · `python scripts/00_setup.py` · [실행·실험 가이드](../guides/training.md#6-실행-및-재현-방법) |
| 교과 7 → 8 인계 (거꾸로 읽을 때) | [`subject7/docs/project/handoff/subject08_handoff.md`](../../../../subject7/docs/project/handoff/subject08_handoff.md) |

## 3. Bridge Holdout — 교과 14 의 몫

| 항목 | 값 |
|---|---|
| 장수 | **156장** (`manifests/bridge_holdout.csv`) |
| 촬영 묶음 | G10 · G11 · G12 + G00 6장 |
| Class 별 박스 | 나뭇잎·종이 202 · 플라스틱·돌·금속 326 · 나뭇가지 281 · 벌레 29 · 갈변 16 · 파·고추 30 |
| 교과 8 에서의 사용 | **없음** — 학습 · 튜닝 · 모델 선택 · Frozen Test 어디에도 쓰지 않았다. `configs/dataset.yaml` 에도 넣지 않았다 |

- 교과 14 에서 처음 쓰는 데이터이므로, **교과 14 의 첫 평가는 `exp050` 을 Bridge 156장에 한 번 돌린 값**이 됩니다. 그 점수를 보고 교과 8 모델을 고르면 Bridge 가 Test 와 같은 처지가 되므로, 다시 고를 일이 있으면 교과 14 안의 새 Validation 으로 합니다.
- Bridge 사진이 있는 PC 에서만 평가할 수 있습니다 (`00_setup.py` 가 `data/bridge_holdout/` 를 만든다). 사진은 Git 에 없습니다.
- 평가 명령은 [`scripts/17_evaluate_bridge.py`](../../scripts/17_evaluate_bridge.md) 가 준비돼 있습니다. **교과 8 에서는 실행하지 않았습니다.**

```bash
python scripts/17_evaluate_bridge.py --dry-run       # 확인만: Manifest 156장 = 폴더 사진·라벨 개수 (모델을 쓰지 않음)
python scripts/17_evaluate_bridge.py --subject14     # 교과 14 에서 처음 한 번 평가 → reports/06_subject14/bridge_metrics.csv
```
- Bridge 에도 갈변은 16박스뿐이라 갈변 Recall 은 박스 1개에 6%p 씩 움직입니다 (아래 5장).

## 4. 새 사진에 Final Model 쓰는 법

```bash
cd ~/group_3/subject8
source .venv/bin/activate
python scripts/08_predict_images.py --model final --source <사진 1장>.jpg --conf 0.25
```

- `--source` 에 **사진 폴더**도 줄 수 있습니다. 정답 TXT 가 같은 이름으로 있으면 정답과 비교하고, 없으면 예측만 그립니다.
- `--source` 없이 `--model final` 만 주면 Validation 104장 전체를 정답과 나란히 예측합니다 (`--limit 5` 로 앞 5장만). 2026-10-20 결과: 예측 538개 · 정답 541개 · **TP 506 · FN 34 · FP 31 · Class 틀림 1** — 상세 [`failure_hypothesis.md`](../../../reports/03_failure_analysis/failure_hypothesis.md) 6장.
- Frozen Test · Bridge 사진은 `--allow-test` 없이는 예측하지 않습니다.
- 사진은 한 장씩 예측합니다. (예전에는 목록째 넘겨 imgsz 2240 에서 Val 전체를 돌리면 GPU 메모리가 넘쳤다 — 2026-10-20 수정)

- `--model final` 이면 imgsz 2240 이 자동으로 정해집니다 (`src/registry.py`). Weight 만 따로 쓸 때는 **학습 때와 같은 imgsz 2240** 으로 예측해야 합니다. 이 모델을 더 큰 해상도(2560 · 2880)로 예측해도 점수는 같고 느려지기만 했습니다 (Val 0.749 → 0.751 → 0.749, 37 → 49 → 61ms/장).
- 신뢰도 기준 `conf` 는 0.25 로 평가했습니다. 낮추면 FN 이 줄고 FP 가 늘어납니다 — 현장에서는 FN(이물을 놓침)이 더 위험한지 FP(정상을 불량 처리)가 더 위험한지부터 정하고 `conf` 를 고릅니다. 이 기준은 교과 14 에서 정해야 하며, 교과 8 에서는 정하지 않았습니다.
- 결과는 `runs/predict/` 에 저장되고 Git 에서 제외됩니다 (사진이 섞임).
- 웹 시연(`app/server.py`)에서 **YOLO TXT 후보 저장**을 지원합니다. 전용 배치 도구(`src/auto_labeler.py`, `scripts/12_auto_label.py`)와 사람 검수 연계는 미완성입니다. 후보는 교과 7 도구에서 사람이 확인·수정·승인한 뒤에 정답으로 씁니다.

## 5. 한계 — 교과 14 에서 먼저 알아야 할 것

숫자는 Frozen Test(82장) 기준 [`final_class_metrics.csv`](../../../reports/05_final/final_class_metrics.csv) 입니다.

| Class | 박스 | Recall | mAP50-95 | 읽는 법 |
|---|---:|---:|---:|---|
| 0 나뭇잎·종이 | 23 | 0.86 | 0.48 | 놓치는 것은 적지만 **Precision 0.37** — 없는 곳에 잎·종이를 자주 찾는다 (FP) |
| 1 플라스틱·돌·금속 | 140 | 0.93 | 0.84 | 안정적 |
| 2 나뭇가지 | 200 | 0.77 | 0.84 | 안정적, 일부 놓침 |
| 3 벌레 | 23 | 0.91 | 0.76 | 박스 23개뿐이라 불안정 |
| 4 고무장갑 | 0 | - | - | 사용하지 않는 Class (ID 유지, 평가 불가) |
| **5 병해·갈변** | 16 | **0.00** | **0.007** | **사실상 못 찾는다** |
| 6 파·고추 | 30 | 1.00 | 0.91 | 좋지만 G00 묶음을 Train 과 나눠 써서 높게 나왔을 수 있다 |

1. **갈변(Class 5)은 이번 모델로 검출할 수 없다고 봐야 합니다.** Val 에서도 Recall 0.13 이었고, Test 에서는 0 입니다. 원인은 주로 데이터입니다 — Train 갈변은 대부분 잎 전체가 변한 것(200px 이상)이고, 평가 데이터의 갈변은 작은 반점(약 25px)입니다. 반점 복제 · 합성 · 복원 · 해상도 2560 등 4라운드 6방향 × seed 5개로 시도했으나 모두 B(0.108)와 같은 범위였습니다. 상세 [`final_model_selection.md`](../../../reports/final_model_selection.md) 「갈변」.
   - 다음에 필요한 것: ① 작은 반점을 Train · Val · Test 에 **같은 기준으로** 라벨링 ② 반점 사진 추가 수집 ③ "잎 전체 갈변"과 "작은 반점"을 Class 로 나눌지 회사와 결정.
   - **Final 뒤 진단 (5라운드, exp063 · seed 1개)**: P2 검출층 + 변형 반점 합성으로 Val 갈변 0.107 → **0.237** (반점 15개 중 14개에 후보). 다만 다른 Class 가 모두 떨어져 전체 0.725 (같은 seed B 0.746) — P2 를 넣으며 검출 head 전체(파라미터 37.5%)가 COCO 사전학습 없이 시작한 것이 원인으로 보인다. 교과 14 에서 이어 갈 방향: head 가중치를 새 층 번호에 맞춰 옮기기 · epoch 늘리기 · P2 만 / 합성만 seed 반복 (`exp051~060` 등록됨). 상세 [`experiment_handoff.md`](../experiment_handoff.md) 10장.
2. **정상 김치(Negative) 사진이 데이터에 없습니다.** 정상 김치에서 오검출(FP)이 얼마나 나는지 교과 8 에서는 측정하지 못했습니다. 제조 현장은 대부분이 정상이라 **교과 14 에서 가장 먼저 모아야 할 데이터**입니다.
   - 힌트: Final 이 Validation 에서 이물 없는 곳에 낸 박스(FP_BACKGROUND) 14건을 눈으로 보면 **사진 가장자리의 어두운 띠**(작업대·트레이)를 플라스틱으로, **짙은 초록 줄기 조각**을 파·고추로 읽은 것이 눈에 띕니다 (확정 아님 — 사진으로 확인 필요, [`failure_hypothesis.md`](../../../reports/03_failure_analysis/failure_hypothesis.md) 6장). 갈변으로 예측한 2건은 빠진 라벨일 수 있습니다.
3. **평가 점수는 "처음 보는 물체"가 아닙니다.** 촬영 팀이 같은 소품을 여러 날 다시 썼고 이물 단독 사진(G17, Train)에 대부분이 들어 있어, 점수는 "본 물체를 새 장면에 놓았을 때"의 성능입니다. 새 소품 · 새 조명 · 새 날짜의 성능은 교과 14 에서 처음 확인됩니다.
4. **Class 0~6 에 없는 이물(머리카락 · 실 등)은 검출 대상이 아닙니다.** 회사 Class 정의에 없어 라벨을 그리지 않았습니다. 교과 14 에서 Class 를 추가할지 회사와 확인합니다 (추가하면 Dataset Version 을 올리고, 기존 ID 를 당기지 않도록 새 ID 는 뒤에 붙이는 것을 권합니다).
5. **평가 역할의 박스 수가 적습니다.** 갈변 · 벌레는 15~30박스뿐이라 박스 1개가 Recall 3~7%p 를 움직입니다. 작은 차이를 개선으로 해석하지 않습니다.
6. **이 모델은 교과 14 의 실시간 판정용으로 최적화되지 않았습니다.** 2240 해상도에서 37ms/장(RTX 3060)이고 TensorRT · Jetson · 양자화는 하지 않았습니다. 라인 속도 요구가 정해지면 가벼운 후보(`exp012` 11s · 1280, 학습 18분, 점수는 낮음)와 비교합니다.

## 6. 지켜야 할 것 (교과 8 에서 가져가는 규칙)

- **Class ID 0~6 을 바꾸지 않습니다.** 4번(고무장갑)은 쓰지 않아도 번호를 당기지 않습니다.
- **GT 를 고치면 Dataset Version 을 올립니다** (`kimchi_v5 → kimchi_v6`). Version 이 다르면 Val · Test 가 달라지므로 점수를 직접 비교하지 않습니다 (예: v4 의 높은 Val 점수는 같은 촬영 묶음 누수 때문이었습니다).
- **Test 점수를 보고 모델을 고치지 않습니다.** Frozen Test 는 `kimchi_v5` 에서 이미 정식으로 한 번 사용되었습니다(그 전에 한 번 본 적도 있음) — 같은 82장으로 다시 모델을 고르면 Test 가 Validation 이 됩니다.
- **한 번에 변수 하나만** 바꿔 비교하고, 실패한 실험도 `experiment_log.csv` 에 남깁니다.
- **Auto Label 은 후보입니다.** 사람이 확인 · 수정 · 승인한 뒤에만 Final Label 이 됩니다.
- **사진을 외부 저장소 · 클라우드 · 메신저에 올리지 않습니다.**

## 7. 처음 받는 팀원이 확인할 순서

1. `git clone https://github.com/ariuck/group_3.git` → `cd group_3/subject8`
2. 회사 원본 사진을 USB 로 `subject7/data/raw/` 에 복사 → `python3 scripts/00_setup.py` → 마지막 줄 `같은 데이터 · 같은 분할 ✓`
3. `python scripts/01_check_environment.py` — PyTorch · Ultralytics · GPU 확인
4. `python scripts/08_predict_images.py --model final --limit 5` — 비교 이미지에서 BBox · Class · Confidence 확인
5. `python scripts/qa_acceptance_check.py` — 자동 점검. 결과 해석은 [`reports/05_acceptance/acceptance_test.md`](../../../reports/05_acceptance/acceptance_test.md)
6. 막힌 곳이나 문서와 실제가 다른 곳은 `acceptance_test.md` 의 재현 시험 표에 적습니다.

## 8. 교과 14 가 이어서 할 일 (제안)

| 순서 | 할 일 | 이유 |
|---|---|---|
| 1 | Bridge Holdout 156장에 Final Model 을 한 번 평가하고 Class 별로 기록 — `python scripts/17_evaluate_bridge.py --subject14` | 처음 보는 데이터에서 실제 성능 확인 (5장 3번) |
| 2 | 정상 김치(Negative) 사진 수집 · FP 율 측정 | 5장 2번 — 현장 비율과 가장 큰 차이 |
| 3 | `conf` 기준 정하기 (FN 과 FP 중 무엇이 더 위험한가) | 4장 |
| 4 | 갈변 데이터 보강 후 Class 5 만 다시 측정 | 5장 1번 |
| 5 | 속도 요구가 정해지면 경량 모델 · 배포 검토 | 5장 6번 |
