# 객체검출 실행·실험 가이드

[← 교과 8](../../../README.md) · [프로젝트 문서](../README.md)

명령과 데이터 경로는 별도 표기가 없으면 `subject8/` 기준입니다. 현재 결과를 빠르게 보려면 [교과 8 README](../../../README.md), 모든 실험과 근거는 [보고서 목차](../../../reports/README.md)를 봅니다.

## 1. 프로젝트 목적

교과 7 에서 검수·확정한 정답 데이터(JPG 900장 + YOLO TXT 900개)로 YOLO11 객체검출 모델(Baseline 11n → Final 11s)을 학습하고,

```text
Dataset Audit → Split → Smoke Test → Baseline → Validation 평가
→ Failure Analysis → 한 변수 개선 → Baseline vs Improved 비교
→ Final Model → Frozen Test → Detection · Auto Label → Human Review
```

까지 수행한 교과 8의 종료 결과를 기록합니다. 교과 14의 대상·모델·진행 방향은 미정입니다.

## 2. 교과 7 → 교과 8 연결

| 항목 | 내용 |
|---|---|
| 교과 7 FINAL 라벨 | `../subject7/data/final/labels/` (Git) — 복사하지 않고 직접 읽음, 직접 수정하지 않음 (고친 라벨은 `data/label_fixes/`) |
| 사진 | `../subject7/data/raw/` 의 회사 원본 (각 PC) — 파일명으로 찾음 |
| 검수 기록 | `../subject7/data/final/검수표.csv` (900행, Git) |
| QA 결과 | [QA Summary](../../../../subject7/reports/qa_summary.md) — FAIL 0 · REVIEW 0 · **교과 8 사용 가능** |
| 인계 문서 | [교과 8 Handoff](../../../../subject7/docs/project/handoff/subject08_handoff.md) |

교과 8 에서 지키는 것:

- Class ID 0~6 과 BBox 기준을 그대로 사용합니다. 900장을 다시 라벨링하지 않습니다.
- `출처 데이터셋`, `원래 split`, `이미지 유형(scene_type)` 정보를 삭제·변경하지 않습니다.
- GT 라벨을 수정하면 Dataset Version 을 올립니다. (예: `kimchi_v1 → kimchi_v2`)

## 3. Dataset 설명

교과 7 FINAL 구조 (원래의 train / validation 구분을 폴더로 유지):

```text
data/final/
├── images/train/        720장
├── images/validation/   180장
├── labels/train/        720개
├── labels/validation/   180개
├── classes.txt
└── 검수표.csv
```

| 출처 데이터셋 | 원래 split | 사진 |
|---|---|---:|
| 이물검출_학습데이터1 | train | 500 |
| 이물검출_학습데이터2 | train | 220 |
| 이물검출_학습데이터2 | validation | 180 |
| **합계** | | **900** |

Data Audit 결과 (`scripts/02_audit_subject7_final.py` → `reports/01_data/audit_summary.csv`, `reports/01_data/audit_issue.csv`):

| 확인 항목 | 결과 |
|---|---|
| JPG / TXT | 900 / 900 |
| 이미지 ↔ TXT Pair 오류 | 0 |
| Empty Label | 0 |
| 형식·Class 범위·좌표·사진 밖 BBox·이름 중복 오류 | 0 |
| 사진 1장당 BBox | 1~12개, 평균 5.07 (537장이 정확히 5개) |
| BBox 합계 | 4561 |

| scene_type (검수표 `이미지 유형`) | 사진 |
|---|---:|
| 김치+대상 객체 (`kimchi_with_target`) | 749 |
| 대상 객체 단독 (`object_only`) | 150 |
| 판단 어려움 (`other_review`) | 1 |
| 정상 김치 (`normal_kimchi`) | 0 |

> 정상 김치(이물 없음) 이미지와 빈 TXT 가 0장입니다. Negative Sample 이 없으므로 FP 분석 때 참고합니다.

## 4. Class

| ID | 한글 | 영문 (`dataset.yaml`) | BBox 수 | BBox 포함 사진 | 사용 |
|---:|---|---|---:|---:|---|
| 0 | 나뭇잎·종이류 | leaf_paper | 727 | 285 | O |
| 1 | 플라스틱류·돌·금속류 | plastic_stone_metal | 1852 | 596 | O |
| 2 | 나뭇가지류 | branch | 932 | 372 | O |
| 3 | 벌레류 | insect | 379 | 197 | O |
| 4 | 고무장갑 | rubber_glove_unused | 0 | 0 | X (ID 유지) |
| 5 | 병해·갈변 | disease_browning | 416 | 198 | O |
| 6 | 파·고추 | green_onion_pepper | 255 | 54 | O |

- Class 4 는 사용하지 않지만 번호를 당기지 않습니다. Instance 0건이므로 Class 별 성능은 `미사용 Class / Instance 0건` 으로 기록합니다.
- Class 6 은 사진 54장으로 가장 적고, 그중 50장이 한 촬영 묶음(G00)에 있습니다. → [Split 정책](../split_policy.md) 5장

## 5. 실행환경

| 항목 | 값 |
|---|---|
| OS | Windows 11 + WSL2 (Ubuntu) |
| GPU | NVIDIA GeForce RTX 3060 (Driver 591.86) |
| Python | 3.14.4 (`subject8/.venv`) |
| PyTorch | 2.14.1+cu130 |
| Ultralytics | 8.4.175 |
| CUDA available | True |
| `YOLO("yolo11n.pt")` Load | 성공 (COCO 80 Class, 2026-10-12 확인) |

## 6. 실행 및 재현 방법

모든 Script 는 이 폴더(`subject8/`)에서 실행합니다. `configs/dataset.yaml` 의 `path: data/yolo` 도 이 위치 기준입니다.

### 6.1 가상환경 · 의존성

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Python / PyTorch / Ultralytics / CUDA 확인 + YOLO11n Load
python scripts/01_check_environment.py
```

### 6.2 다른 PC 에서 시작하기 · Git 에 올리는 것

**Git 에 올리는 것 / 올리지 않는 것** (`subject8/.gitignore`)

| 올림 ✅ | 올리지 않음 ❌ |
|---|---|
| 교과 7 FINAL 라벨 `subject7/data/final/labels/**/*.txt` (900개), `검수표.csv`, `classes.txt` | **김치·이물 사진** (`*.jpg` 등, 어느 폴더든) · `subject7/data/raw`·`work` |
| 라벨 수정본 `data/label_fixes/kimchi_v3`·`kimchi_v5/*.txt` (v3~v5 재현에 필요) | `data/yolo*/`, `data/bridge_holdout*/`, `data/smoke/` — 03·05 가 다시 만듦 |
| 모델 Weight `models/**/*.pt` (실험마다 best 1개, 약 5MB) — 목록 [`models/README.md`](../../../models/README.md) | `runs/*/weights/` (models/ 와 중복), `yolo11n.pt` (자동 다운로드) |
| `runs/<실행>/results.csv`·`args.yaml`·그래프(`*.png`, `labels.jpg` — Confusion Matrix · PR 곡선 등, 실행당 약 1.6MB) | `runs/*/*_batch*.jpg` (김치 사진 미리보기) · `runs/eval`·`runs/predict` (사진 섞임) |
| 그래프 `reports/figures/` (실행별 학습 곡선은 `plot_runs.py` 로 생성, 약 0.1MB) | `demo/` 의 사진 모음 |
| manifest·보고서·문서, `.vscode/` 공통 설정 | `.venv/` |

**다른 PC 에서 처음 받을 때**

```bash
git clone https://github.com/ariuck/group_3.git ~/group_3     # 이미 받았으면 git pull
cd ~/group_3/subject8

# 회사 원본(사진 + 원본 라벨) 폴더를 그대로 subject7/data/raw 에 복사 (USB 등 — 승인된 전달 경로 사용)
#   subject7/data/raw/이물검출_학습데이터1/images/train/*.jpg …, 이물검출_학습데이터2/…
cp -r <USB>/이물검출_학습데이터1 <USB>/이물검출_학습데이터2 ../subject7/data/raw/

# 올인원: subject8/.venv · subject7/.venv → 교과 7 복원(work·검수표·final) → 점검 → kimchi_v4·v5 학습 폴더 → Git 과 같은지 확인
python3 scripts/00_setup.py      # 이미 준비된 PC 에서 다시 실행해도 된다 (된 단계는 건너뜀, 약 7초)
```

마지막에 `같은 데이터 · 같은 분할 ✓` 이 나오면 끝입니다. 단계별 설명: [`docs/scripts/00_setup.md`](../../scripts/00_setup.md)

- VSCode 는 이 폴더를 직접 엽니다 (`code ~/group_3/subject8`). `.vscode/` 설정이 Git 에 있어 `.venv` 인터프리터·실행 메뉴(F5)가 바로 잡힙니다.
- 모델이 Git 에 있으므로 학습 없이 바로 평가·예측할 수 있습니다 (`07`, `08`, `09`).
- 교과 8 은 사진을 `subject7/data/raw` 아래에서 파일명으로 찾으므로 하위 폴더 구조는 상관없습니다. 교과 8 만 쓸 거라면 `restore_from_final.py` 는 건너뛰어도 됩니다.

**그래프 정책 (실험이 수십 개가 되어도 저장소가 가볍게)**

| 그래프 | 어디에 | 크기 |
|---|---|---|
| 모든 실행의 학습 곡선 · 같은 Dataset Version 끼리 비교 · 모델 목록 | `python scripts/plot_runs.py` → `reports/figures/runs/<실행>.png`, `reports/figures/comparison/runs_comparison_<Version>.png`, `reports/runs_summary.csv`, `models/README.md` | 실행당 약 0.1MB |
| 실행마다의 Ultralytics 원본 그래프 (Confusion Matrix · PR/P/R/F1 곡선 · results.png) | `runs/<실행>/` (Git 에 올림) | 실행당 약 1.6MB |
| 공식 Baseline 의 Val 평가 그래프 | `07_evaluate_baseline.py` → `reports/figures/baseline/` | 약 1MB |

새 학습을 하면 `python scripts/plot_runs.py` 를 한 번 실행하고 `runs/<실행>/`·`models/…/*.pt`·`reports/` 를 함께 커밋합니다.

### 6.3 2일차 — Data Audit

```bash
python scripts/02_audit_subject7_final.py
```

- 이미지-라벨 1:1 매칭, YOLO 좌표(0~1)·사진 밖 BBox, Class 범위(0~6), 이름 중복, 검수표 대조 전수 검사
- 이미지별 BBox 수, Class × 장면 분포 (가이드 15.1·15.2)
- 촬영 묶음(5분 간격) × 사진 지문(dHash)으로 Data Leakage 확인 (가이드 15.3)
- 산출물: `reports/01_data/audit_summary.csv`, `reports/01_data/audit_issue.csv`, `reports/01_data/audit_class_scene.csv`, `reports/01_data/leakage_check.csv`, `reports/01_data/capture_group_summary.csv`

### 6.4 3일차 — Dataset Split & Freeze

```bash
python scripts/03_build_split.py                                   # 공식 Version(kimchi_v5) manifest · dataset.yaml · dataset_summary
python scripts/03_build_split.py --copy-files                      # data/yolo/, data/bridge_holdout/ 실제 폴더까지 (기존 폴더는 지우고 다시)
python scripts/03_build_split.py --version kimchi_v4 --copy-files  # 지난 Version → data/yolo_v4 · manifests/kimchi_v4/ (공식 폴더는 그대로)
```

보통은 `00_setup.py` 가 v4·v5 를 한 번에 만듭니다. 공식 Version 은 `src/constants.py` 의 `DEFAULT_DATASET_VERSION` 한 곳에서 정하고, 공식만 가이드 이름 폴더를 씁니다.

### 6.5 3일차 — Smoke Test

```bash
python scripts/05_smoke_train.py              # Train 40 / Val 8, 3 epoch → Prediction 1장
python scripts/05_smoke_train.py --overwrite  # 다시 할 때
```

- 결과: `reports/history/smoke_test.md` (점검 7항목), `runs/smoke_v1/`, `configs/smoke_dataset.yaml`
- Smoke Weight 는 Baseline 이 아닙니다.

### 6.6 Baseline 학습 (공식: `baseline_v5`)

```bash
python scripts/06_train_baseline.py                       # 공식 Version → baseline_v5 (이미 있으면 멈춤)
python scripts/06_train_baseline.py --version kimchi_v4   # 지난 Version 재현
```

- 조건은 스크립트 맨 위 `BASELINE` 한 곳에서만 정합니다 (YOLO11n · epoch 50 · imgsz 640 · batch 16 · seed 42 · AdamW · lr0 0.001).
- 결과: `runs/baseline_v5/`, `models/baseline/baseline_v5.pt` (+ 공식 이름 복사본 `baseline_best.pt`), `reports/02_baseline/baseline_training_condition.md`
- 모델 이름 규칙: `models/<역할>/<runs 폴더 이름>.pt`, 지난 Version 은 `models/history/<Version>/` — [`models/README.md`](../../../models/README.md), [`src/registry.py`](../../src/registry.md)

### 6.7 5일차 — Validation 평가 · 이미지 Detection

```bash
python scripts/07_evaluate_baseline.py                                # 공식 Baseline × Val 104장 → reports/02_baseline/
python scripts/08_predict_images.py                                   # 정답·예측 비교 사진 → runs/predict/baseline_v5_val/compare/
python scripts/08_predict_images.py --model exp002_v5_imgsz1920       # 다른 모델 (imgsz · Val 폴더 자동)
python scripts/08_predict_images.py --conf 0.5 --limit 10             # 기준을 바꿔 보기
```

- Frozen Test·Bridge 사진은 막혀 있습니다 (8일차에 `--allow-test`).

### 6.8 6일차 — Failure Analysis

```bash
python scripts/09_collect_failures.py                                 # 공식 Baseline
python scripts/09_collect_failures.py --model exp002_v5_imgsz1920     # 다른 모델
```

- 결과: `reports/03_failure_analysis/failure_*.csv`, `demo/failure_analysis/*.jpg` (대표 실패 사진, Git 제외)

### 6.9 개선 실험 (공식 kimchi_v5)

```bash
python scripts/11_train_v5.py --run exp001          # 해상도 · epoch · 증강 (06 조건에서 한 변수만)
python scripts/14_train_tiles_v5.py                 # 타일링 (2×2 조각 학습 → 원본 Val 채점)
python scripts/plot_runs.py                         # 그래프 · runs_summary.csv · models/README.md
```

- 실험 판정: [`reports/04_improvement/experiment_log.csv`](../../../reports/04_improvement/experiment_log.csv), 조건 기록: `reports/04_improvement/<실행>_training_condition.md`
- 지난 Version 실험 재현: `python scripts/10_train_v2.py [--exp exp002] [--version kimchi_v4]`

### 6.10 라벨 수정 → 새 Dataset Version

- `kimchi_v3`: Class 5(갈변) 기준 개정 — 라벨링 프로그램에서 고친 TXT 를 `04_import_label_fixes.py` 로 `data/label_fixes/kimchi_v3/` 에 가져옴. 기준 [`class_guide.md`](../../../../subject7/docs/project/standards/class_guide.md) Class 5 "검출 대상 범위", 작업 목록 `reports/01_data/label_fixes_kimchi_v3/`
- `kimchi_v5`: v3 + 이물이 없는 박스 3개 삭제 (`data/label_fixes/kimchi_v5/`, 기록 `reports/01_data/label_fixes_kimchi_v5/`)
- 교과 7 최종본(`subject7/data/final`)은 고치지 않고, Version 별 수정본 폴더만 둡니다.

## 7. Dataset Split (`kimchi_v5` = C안 재분할, 공식)

- **정책**: 촬영 간격 5분 초과로 나눈 18개 `capture_group` 을 **통째로** 배정, 예외는 파·고추(Class 6)가 몰린 `G00` 하나 (구간별 시간순 블록). 평가 역할마다 Class 별 15박스 이상, 그 조건에서 Train 이 가장 큰 조합
- **v4 → v5 이유**: v4 는 Val 132장 중 83장이 Train 과 같은 촬영 묶음 → v5 는 6장(G00 예외)뿐. v4 의 높은 Val 점수(특히 갈변)는 이미 본 장면으로 잰 값이었음 — [`docs/project/kimchi_v5_split.md`](../kimchi_v5_split.md), 비교 그림 `reports/figures/comparison/v5_vs_v4.png`
- 버전: `kimchi_v1`(2026-10-12) → `v2`(분할) → `v3`(Class 5 라벨 개정) → `v4`(G09 분할) → **`v5`(재분할, 2026-10-16)**. Version 마다 Val 이 달라 Validation 점수는 직접 비교하지 않습니다. 지난 Version: [split_policy.md](../split_policy.md), `reports/history/`
- Bridge Holdout 은 교과 8 학습·튜닝·모델 선택·Frozen Test 에 사용하지 않고 후속 활용을 위해 보존합니다. `dataset.yaml` 에 넣지 않습니다.

| 역할 | 장수 | C0 | C1 | C2 | C3 | C5 | C6 | 촬영 묶음 | 용도 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Train | 558 | 308 | 1120 | 427 | 311 | 209 | 165 | G01~04 · G06 · G08 · G09 · G15~17 + G00 일부 | 모델 학습 (이물 단독 150장 포함) |
| Validation | 104 | 192 | 265 | 23 | 16 | 15 | 30 | G05 · G13 + G00 6장 | 실험 비교 · Final 선택 |
| Frozen Test | 82 | 23 | 140 | 200 | 23 | 16 | 30 | G07 · G14 + G00 6장 | Final Model 확정 후 마지막 평가 |
| Bridge Holdout | 156 | 202 | 326 | 281 | 29 | 16 | 30 | G10 · G11 · G12 + G00 6장 | 미사용 보존·후속 방향 미정 |

*(숫자는 BBox 수)*

산출물 1: `configs/dataset.yaml`, `manifests/split_manifest.csv`, `manifests/{train,val,test,bridge_holdout}.csv`, `docs/project/kimchi_v5_split.md`, `reports/01_data/dataset_summary.csv`

## 8. Baseline (`baseline_v5` — kimchi_v5 · YOLO11n · imgsz 640)

- 학습: 2026-10-16, 50 epoch · 약 5분 — [`reports/02_baseline/baseline_training_condition.md`](../../../reports/02_baseline/baseline_training_condition.md), `models/baseline/baseline_best.pt` (= `baseline_v5.pt`)
- Validation 평가 (104장 · 정답 BBox 541개) — [`reports/02_baseline/baseline_metrics.csv`](../../../reports/02_baseline/baseline_metrics.csv), [`baseline_class_metrics.csv`](../../../reports/02_baseline/baseline_class_metrics.csv), 그래프 `reports/figures/baseline/`
- 아래 0.471 은 학습이 끝난 뒤 `07_evaluate_baseline.py` 로 다시 잰 값(0.4707)이고, 개선 실험 비교표의 **0.470** 은 학습 중 best epoch 44 의 값(0.4695)이다. 측정이 달라 소수 셋째 자리가 다르다 (실험끼리는 학습 중 값으로 비교)

| Precision | Recall | mAP50 | mAP50-95 |
|---:|---:|---:|---:|
| 0.888 | 0.589 | 0.687 | 0.471 |

| Class | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| 0 leaf_paper | 0.922 | 0.797 | 0.883 | 0.657 |
| 1 plastic_stone_metal | 0.868 | 0.513 | 0.742 | 0.457 |
| 2 branch | 0.832 | 0.644 | 0.720 | 0.538 |
| 3 insect | 0.785 | 0.812 | 0.856 | 0.463 |
| 4 rubber_glove_unused | - | - | - | - (Instance 0건) |
| 5 disease_browning | 1.000 | 0.000 | 0.000 | 0.000 |
| 6 green_onion_pepper | 0.920 | 0.767 | 0.923 | 0.710 |

- 지난 Baseline: `baseline_v1` (Val 84장, mAP50-95 0.351), `baseline_v4` (Val 132장, 0.538) — `reports/history/<Version>/`. Val 이 달라 숫자를 직접 비교하지 않습니다.

## 9. Failure Analysis (`baseline_v5`, Val 104장 · conf 0.25)

근거 표: `reports/03_failure_analysis/failure_*.csv` (`09_collect_failures.py`)

정답 541개 중 TP 395 · 실패 233건 — FN 111 · CLASS_ERROR 35 · FP_DUPLICATE 30 · FP_PARTIAL 33 · FP_BACKGROUND 24

- 가장 많은 실패: 플라스틱·돌 FN 64 · CLASS_ERROR 22, 갈변 FN 15 (15개 전부)
- **갈변**: v5 Val 의 갈변은 대부분 작은 갈색 점(한 변 20~30px)이라 640 에서 3px 안팎 — Train 갈변은 거의 G09 의 넓게 변한 배추 조각. 라벨 기준은 교과 7 `class_guide.md` 대로 그대로 두고 모델 쪽(해상도·타일링)으로 다룸
- 원인 가설 문서: [`reports/03_failure_analysis/failure_hypothesis.md`](../../../reports/03_failure_analysis/failure_hypothesis.md) (v5 기준 H1~H5 · 이후 검증). kimchi_v1 때의 가설(H1~H5): [`reports/history/kimchi_v1/03_failure_analysis/failure_hypothesis.md`](../../../reports/history/kimchi_v1/03_failure_analysis/failure_hypothesis.md)

## 10. Improvement (kimchi_v5, 같은 Val 104장)

실험 비교는 한 변수씩 바꾸는 것을 원칙으로 했으며, 여러 변수를 함께 바꾼 예외는 아래 표와 실험 기록에 따로 표시했습니다. 점수는 학습 중 best epoch 의 Validation mAP50-95 (판정 기준 +0.02). 상세: [`experiment_log.csv`](../../../reports/04_improvement/experiment_log.csv), [`models/README.md`](../../../models/README.md), 비교 그림 `reports/figures/comparison/runs_comparison_kimchi_v5.png`

| 실험 | 바꾼 것 | P | R | mAP50 | mAP50-95 | 판정 |
|---|---|---:|---:|---:|---:|---|
| baseline_v5 | — (imgsz 640) | 0.888 | 0.589 | 0.688 | 0.470 | 공식 Baseline |
| exp001_v5 | imgsz 640 → 1280 | 0.957 | 0.724 | 0.777 | 0.646 | 채택 (+0.177) |
| **exp002_v5** | imgsz 1280 → 1920 (batch 6) | 0.856 | 0.766 | 0.809 | **0.704** | 채택 (+0.058) |
| exp003_v5 | exp002 + epochs 50 → 100 | 0.872 | 0.788 | 0.801 | 0.701 | 기각 (-0.003, 시간 2배) |
| exp005_v5 | exp002 + 증강 (상하반전 · 밝기) | 0.841 | 0.760 | 0.800 | 0.684 | 기각 (-0.020) |
| exp004_v5 | exp002 입력을 2×2 조각으로 (타일링) | 0.829* | 0.814* | 0.799* | 0.698* | 보류 (+0.019*, Recall +0.033) |
| exp006_v5 | exp005 + imgsz 2560 (두 변수†) | 0.872 | 0.814 | 0.832 | 0.722 | 보류 (exp005 대비 +0.038, 학습 5시간) |
| **exp007_v5** | exp005 + **YOLO11s** (두 변수†) | 0.956 | 0.794 | 0.824 | **0.724** | 채택 후보 (exp005 대비 +0.040, 43분) |

† exp006·exp007 은 exp002 대비 두 변수(증강 + 해상도 / 모델 크기)를 함께 바꾼 실험 (사용자 결정). exp005 와는 한 변수만 달라 각 효과를 따로 읽는다. 둘 다 best epoch 가 마지막 근처라 아직 오르는 중.

\* 타일링은 학습 중 Val 이 조각 단위라, 조각 예측을 합쳐 원본 Val 104장을 같은 코드(`src/tiling.py`)로 채점한 값 — 같은 코드로 잰 exp002_v5 는 0.680. [`tiling_eval.csv`](../../../reports/04_improvement/tiling_eval.csv)

- 개선점·한계 정리 (발표용): [`reports/04_improvement/baseline_vs_improved.md`](../../../reports/04_improvement/baseline_vs_improved.md)
- 1라운드(3대) 결과: epoch 100 · 타일링 · 1280 · TTA 모두 이득 없음, seed 흔들림 ±0.01, 다른 PC 재현성 확인 — 2라운드(6명, Final 후보 3개 × seed) 계획: [`docs/project/experiment_handoff.md`](../experiment_handoff.md)
- 2~4라운드(exp009 · 011 · 014~050): 후보 B(11s · 2240) 선택 → 갈변 개선 6방향 × seed 5개 모두 B 보다 +0.02 못 미침 → **Final = B 의 exp050**. 전체 설계·결과 [`reports/04_improvement/improvement_experiment.md`](../../../reports/04_improvement/improvement_experiment.md)
- 지난 Version(v4) 개선 분석: [`reports/history/kimchi_v4/baseline_vs_improved.md`](../../../reports/history/kimchi_v4/baseline_vs_improved.md)

## 11. Final Model (2026-10-20 확정)

**`exp050_v5_s_imgsz2240_aug_seed2`** → `models/final/final_best.pt` (`src/registry.py` 의 `OFFICIAL["final"]`)

| 항목 | 값 |
|---|---|
| 조건 | YOLO11s · imgsz 2240 · batch 2 · epoch 50 · 증강(flipud 0.5 · hsv_v 0.6) · seed 2 · 학습 62분 (RTX 3060) |
| Validation (best epoch 50) | P 0.945 · R 0.822 · mAP50 0.840 · mAP50-95 **0.749** (Baseline 0.470) |
| 선택 이유 | 후보 B(11s · 2240) seed 5개 평균 0.739 가 A(11s · 1920) 0.715 보다 +0.024, 4라운드 6방향 중 B 보다 +0.02 오른 것이 없어 B 그대로 · B 안에서 Val 최고. Val 최고는 seed 5개 중 고른 값이라 부풀어 있다 |
| 추론 설정 | 기본 (TTA · agnostic NMS 는 손해) · 예측 약 37ms/장 |

근거: [`reports/final_model_selection.md`](../../../reports/final_model_selection.md) (후보별 평균 · Class 별 · 갈변 분석) · 실험 전체 [`reports/04_improvement/improvement_experiment.md`](../../../reports/04_improvement/improvement_experiment.md) · 52개 실험 기록 [`experiment_log.csv`](../../../reports/04_improvement/experiment_log.csv)

## 12. Frozen Test (Final 확정 뒤 한 번 · 82장)

[`reports/05_final/final_metrics.csv`](../../../reports/05_final/final_metrics.csv) · [`final_class_metrics.csv`](../../../reports/05_final/final_class_metrics.csv) · 그림 `reports/figures/final/`

| Precision | Recall | mAP50 | mAP50-95 |
|---:|---:|---:|---:|
| 0.868 | 0.744 | 0.726 | **0.639** |

| Class | 박스 | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| 0 leaf_paper | 23 | 0.367 | 0.855 | 0.521 | 0.482 |
| 1 plastic_stone_metal | 140 | 0.979 | 0.929 | 0.949 | 0.840 |
| 2 branch | 200 | 0.981 | 0.768 | 0.930 | 0.839 |
| 3 insect | 23 | 0.893 | 0.913 | 0.946 | 0.756 |
| 4 rubber_glove_unused | 0 | - | - | - | - (Instance 0건) |
| 5 disease_browning | 16 | 1.000 | **0.000** | 0.015 | **0.007** |
| 6 green_onion_pepper | 30 | 0.987 | 1.000 | 0.995 | 0.908 |

- **대외 성능은 Test mAP50-95 0.639 로 말한다.** Val 0.749 는 최고 seed 를 고른 값이라 부풀었고 Test 는 다른 촬영 묶음(G07 · G14)이다.
- **갈변은 사실상 검출하지 못한다** (Recall 0.00). 나뭇잎·종이는 Precision 0.37 로 오검출이 많다. 상세 [`docs/project/handoff/subject14_handoff.md`](../handoff/subject14_handoff.md) 5장.
- Test 점수로 모델을 다시 고르지 않았다. 다만 2026-10-16 Final 확정 전에 Test 점수를 한 번 본 적이 있다는 기록이 있다 ([`baseline_vs_improved.md`](../../../reports/04_improvement/baseline_vs_improved.md) 3장 — 그 점수로 모델·조건을 고르지는 않았다).

## 13. Detection / Auto Label

**Detection — 동작함.** 사진을 정답(GT)과 나란히 예측해 BBox · Class · Confidence 를 그린다.

```bash
python scripts/08_predict_images.py --model final --limit 5          # Final 모델로 Validation 사진 5장 (imgsz 2240 자동)
python scripts/08_predict_images.py --model final --source 사진.jpg    # 사진 1장
```

- 결과: `runs/predict/exp050_v5_s_imgsz2240_aug_seed2_val/compare/*.jpg` (왼쪽 정답 · 오른쪽 예측), `predictions.csv`, `per_image.csv` — 사진이라 Git 제외.
- 2026-10-20 확인: **Val 104장 전체** · 예측 538 · 정답 541 · **TP 506 · FN 34 · FP 31 · Class 틀림 1** (Baseline 은 TP 395 · FN 111 · Class 틀림 35). Class 별 대표 사진도 눈으로 확인 ([`acceptance_test.md`](../../../reports/05_acceptance/acceptance_test.md) 4장). Final 의 남은 실패 분석: [`failure_hypothesis.md`](../../../reports/03_failure_analysis/failure_hypothesis.md) 6장.
- 폴더 단위 예측: `--source <사진 폴더>`. 사진은 한 장씩 예측한다 (imgsz 2240 에서 목록째 넘기면 GPU 메모리 초과).
- 보존 Bridge 평가용 기존 도구: `python scripts/17_evaluate_bridge.py --subject14` (교과 8 에서는 실행하지 않음, `--dry-run` 은 개수만 확인).

**시연 프로그램 (FastAPI + 브라우저)** — 본편 15번은 녹화 시연이며 라이브 GUI는 부록 A13 또는 서버 주소로 연다. 설명: [`docs/app/server.md`](../../app/server.md)

```bash
pip install -r requirements.txt          # fastapi · uvicorn 이 없으면 (2026-10-20 추가)
.venv/bin/python app/server.py           # → http://127.0.0.1:8010 (발표자료는 http://127.0.0.1:8010/presentation/)
```

- Validation 사진을 고르면 바로 예측하고 정답과 비교(맞힘 · 종류 틀림 · 오검출 · 놓침), 확신도 기준을 움직이면 판정이 바로 바뀐다. 4K 원본을 휠로 확대해 작은 이물을 볼 수 있다.
- Validation 104장 일괄 채점(약 12초) — 기준 0.25 에서 맞힘 506 · 놓침 34 · 오검출 31 로 `08` · `09` 와 같다.
- 사진 끌어다 놓기 · YOLO TXT 후보 저장(Auto Label 후보 — 사람 검수 후 확정). Frozen Test · Bridge 사진은 거절, 127.0.0.1 전용, 올린 사진은 저장하지 않음.

**Auto Label — 웹 시연에서 YOLO TXT 후보를 저장할 수 있습니다.** 전용 배치 모듈(`src/auto_labeler.py` · `scripts/12_auto_label.py`)과 사람 검수까지 이어지는 전체 자동화는 종료 시점 제공하지 않은 범위입니다. 후보 TXT는 교과 7 라벨링 도구에서 사람이 확인·수정·승인한 뒤에만 정답으로 사용합니다.

## 14. 알려진 한계

- 정상 김치(Negative) 이미지가 없습니다.
- 촬영 팀이 같은 소품(이물)을 날짜를 넘어 다시 썼고 이물 단독 사진(G17, Train)에 소품 대부분이 있어, 평가 점수는 "처음 보는 물체"가 아니라 "본 물체를 새 장면에 놓았을 때" 성능입니다. 평가 사진도 모두 Train 과 같은 날짜에 찍었습니다 ([kimchi_v5_split.md](../kimchi_v5_split.md) 한계).
- Class 6(파·고추)은 G00 한 묶음을 나눠 쓰므로 같은 조각이 Train 과 평가에 함께 나와 점수가 높게 나올 수 있습니다.
- 평가 역할의 갈변·벌레가 15~29박스뿐이라 박스 1개에 Recall 이 3~7%p 움직입니다.
- **머리카락·실 등 Class 0~6 에 없는 이물은 검출 대상이 아닙니다.** 회사 Class 정의에 없어 라벨을 그리지 않았습니다 (`kimchi_v3` 에서 머리카락을 나뭇가지로 그린 BBox 1개 삭제). 후속 작업이 진행된다면 대상·Class 범위를 새로 정해야 합니다.
- **Class 5(갈변)**: Train 갈변은 거의 G09 의 넓게 변한 조각이고, 평가 역할의 갈변은 작은 갈색 점(원본 20~30px)이 많아 현재 모델은 거의 찾지 못합니다 (exp002_v5 Val 갈변 AP50 0.06, 타일링 0.09). 4라운드에서 반점 복제 · 합성 · 복원 · 2560 6방향을 seed 5개씩 시도했지만 갈변 mAP50-95 는 0.075~0.111 로 그대로였고 **Frozen Test 에서는 Recall 0.00** 입니다. 데이터를 늘리는 방법으로는 오르지 않았습니다. Final 뒤 진단(exp063, seed 1개)에서 P2 검출층 + 변형 반점 합성이 Val 갈변을 0.107 → **0.237** 로 올렸지만 다른 Class 가 모두 떨어져 전체 0.725 (같은 seed B 0.746) 라 Final 은 그대로다. 다음은 구조(P2 · head 사전학습)와 같은 기준으로 라벨링한 작은 갈변 데이터 보강입니다 (후속 활용 시 참고 · [`failure_hypothesis.md`](../../../reports/03_failure_analysis/failure_hypothesis.md) H2).
- **Frozen Test 를 한 번 먼저 본 적이 있습니다** (2026-10-16, Final 확정 전 · 그 점수로 모델을 고르지는 않음). 정식 평가는 Final 확정 뒤 한 번입니다 ([`baseline_vs_improved.md`](../../../reports/04_improvement/baseline_vs_improved.md) 3장).
- 5라운드(P2 검출층 · 변형 반점 합성)는 팀 결정으로 exp063 하나만 학습했습니다 (exp051~065 중 나머지 14개는 등록만). 결과와 다른 Class 하락 원인은 [`docs/project/experiment_handoff.md`](../experiment_handoff.md) 10장.

## 15. 후속 활용 참고 (방향 미정)

교과 7·8은 종료했습니다. 현재 김치 모델·데이터를 후속 과제에서 계속 사용할지, 다른 검출 모델로 바꿀지는 정해지지 않았습니다.

기존 [후속 활용 참고 문서](../handoff/subject14_handoff.md)는 Final·미사용 Bridge 156장·알려진 한계·재현 경로를 보존합니다. 교과 14의 필수 인계 조건이나 확정 실행 계획으로 사용하지 않습니다.
