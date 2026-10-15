# AI Campus Subject 8
# 조각김치 이물검출 Object Detection (YOLO11n)

교과 8 `[중간] Vision 기반 객체검출 모듈` 과제 저장소입니다.
교과 7 FINAL 검수 완료 4K 조각김치 데이터셋(900장)을 촬영 회차 누수를 막아 분할하고, YOLO11n 을 파인튜닝하여 교과 14 로 연결합니다.

> **진행 상태**: 3일차 — Dataset Split `kimchi_v1` FROZEN (2026-10-12)
>
> **데이터 성격**: AI캠퍼스 교육을 위해 실제 산업데이터와 유사한 분포 구조로 100% 가상 생성된 조각김치 이물검출 학습데이터를 사용합니다.
>
> **보안**: 김치·이물 **사진만** Git 에 올리지 않습니다. 라벨 TXT·검수표·모델 Weight·학습 기록·그래프는 올려서 다른 PC 에서 같이 작업합니다 (6.2 "Git 에 올리는 것").
>
> 아직 정해지지 않은 값은 `TBD` 로 두고, 실제로 결정·측정한 날 채웁니다. 성능 숫자를 미리 적지 않습니다.

---

## 1. 프로젝트 목적

교과 7 에서 검수·확정한 정답 데이터(JPG 900장 + YOLO TXT 900개)로 YOLO11n 객체검출 모델을 학습하고,

```text
Dataset Audit → Split → Smoke Test → Baseline → Validation 평가
→ Failure Analysis → 한 변수 개선 → Baseline vs Improved 비교
→ Final Model → Frozen Test → Detection · Auto Label → Human Review
```

까지 수행하여 교과 14(제조 제품검사)로 인계합니다.

## 2. 교과 7 → 교과 8 연결

| 항목 | 내용 |
|---|---|
| 교과 7 FINAL 원본 | 저장소 루트 `data/final/` (이 폴더 기준 `../data/final/`) |
| 교과 8 사용 위치 | `data/subject7_final/` — FINAL 을 그대로 복사해 사용, 직접 수정하지 않음 |
| 검수 기록 | `data/subject7_final/검수표.csv` (900행) |
| QA 결과 | [QA Summary](../subject7/reports/qa_summary.md) — FAIL 0 · REVIEW 0 · **교과 8 사용 가능** |
| 인계 문서 | [교과 8 Handoff](../subject7/docs/handoff/subject08_handoff.md) |

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

Data Audit 결과 (`scripts/02_audit_subject7_final.py` → `reports/audit/audit_summary.csv`, `reports/audit/audit_issue.csv`):

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
- Class 6 은 사진 54장으로 가장 적고, 그중 50장이 한 촬영 묶음(G00)에 있습니다. → [Split 정책](docs/split_policy.md) 5장

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
| 교과 7 FINAL 라벨 `data/subject7_final/labels/**/*.txt` (900개), `검수표.csv`, `classes.txt` | **김치·이물 사진** (`*.jpg` 등, 어느 폴더든) |
| 라벨 수정본 `data/label_fixes/kimchi_v3/*.txt` (kimchi_v3·v4 재현에 필요) | `data/yolo/`, `data/bridge_holdout/`, `data/smoke/` — 03·05 가 다시 만듦 |
| 모델 Weight `models/**/*.pt` (실험마다 best 1개, 약 5MB) | `runs/*/weights/` (models/ 와 중복), `yolo11n.pt` (자동 다운로드) |
| `runs/<실행>/results.csv`·`args.yaml` | `runs/*/*.png` 등 Ultralytics 원본 그래프 (실행당 약 1.8MB) · `runs/eval`·`runs/predict` (사진 섞임) |
| 그래프 `reports/figures/` (실행별 학습 곡선은 `plot_runs.py` 로 생성, 약 0.1MB) | `demo/` 의 사진 모음 |
| manifest·보고서·문서, `.vscode/` 공통 설정 | `.venv/` |

**다른 PC 에서 처음 받을 때**

```bash
git clone https://github.com/ariuck/group_3.git ~/group_3
cd ~/group_3/subject8
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 사진만 따로 복사 (USB 등 — 외부 클라우드·메신저 금지). 라벨·검수표는 이미 Git 에 있다
#   원본 PC 의 subject8/data/subject7_final/images/ 를 같은 위치로
cp -r <USB>/images data/subject7_final/images

.venv/bin/python scripts/02_audit_subject7_final.py          # JPG 900 / TXT 900 / 이슈 0 이면 정상
.venv/bin/python scripts/03_build_split.py --copy-files      # kimchi_v4 학습 폴더 생성 (manifest 는 바뀌지 않아야 함)
git status                                                    # 아무것도 바뀌지 않았으면 같은 데이터·같은 분할
```

- VSCode 는 이 폴더를 직접 엽니다 (`code ~/group_3/subject8`). `.vscode/` 설정이 Git 에 있어 `.venv` 인터프리터·실행 메뉴(F5)가 바로 잡힙니다.
- 모델이 Git 에 있으므로 학습 없이 바로 평가·예측할 수 있습니다 (`07`, `08`, `09`).
- 사진 폴더는 평평한 구조(`images/`)와 교과 7 원본 구조(`images/train`, `images/validation`)를 모두 읽습니다.

**그래프 정책 (실험이 수십 개가 되어도 저장소가 가볍게)**

| 그래프 | 어디에 | 크기 |
|---|---|---|
| 모든 실행의 학습 곡선 · 같은 Dataset Version 끼리 비교 | `python scripts/plot_runs.py` → `reports/figures/runs/<실행>.png`, `reports/figures/comparison/runs_comparison_<Version>.png`, `reports/runs_summary.csv` | 실행당 약 0.1MB |
| 핵심 모델(Baseline·Final·발표에 쓸 실험)의 Confusion Matrix · PR 곡선 | `07_evaluate_baseline.py` 처럼 `reports/figures/` 에 복사 | 모델당 약 1MB |
| 그 밖의 Ultralytics 원본 그래프 | `runs/` 에만 (Git 제외). 필요하면 Git 의 모델로 다시 평가해 만든다 | — |

새 학습을 하면 `python scripts/plot_runs.py` 를 한 번 실행하고 `runs/<실행>/results.csv`·`args.yaml`·`models/.../*.pt`·`reports/figures/runs/` 를 함께 커밋합니다.

### 6.3 2일차 — Data Audit

```bash
python scripts/02_audit_subject7_final.py
```

- 이미지-라벨 1:1 매칭, YOLO 좌표(0~1)·사진 밖 BBox, Class 범위(0~6), 이름 중복, 검수표 대조 전수 검사
- 이미지별 BBox 수, Class × 장면 분포 (가이드 15.1·15.2)
- 촬영 묶음(5분 간격) × 사진 지문(dHash)으로 Data Leakage 확인 (가이드 15.3)
- 산출물: `reports/audit/audit_summary.csv`, `reports/audit/audit_issue.csv`, `reports/audit/audit_class_scene.csv`, `reports/audit/leakage_check.csv`, `reports/audit/capture_group_summary.csv`

### 6.4 3일차 — Dataset Split & Freeze

```bash
# manifest · dataset.yaml · dataset_summary 생성
python scripts/03_build_split.py

# data/yolo/, data/bridge_holdout/ 실제 폴더까지 만들 때 (기존 폴더는 지우고 다시 만듦)
python scripts/03_build_split.py --copy-files
```

### 6.5 3일차 — Smoke Test

```bash
python scripts/05_smoke_train.py              # Train 40 / Val 8, 3 epoch → Prediction 1장
python scripts/05_smoke_train.py --overwrite  # 다시 할 때
```

- 결과: `reports/history/smoke_test.md` (점검 7항목), `runs/smoke_v1/`, `configs/smoke_dataset.yaml`
- Smoke Weight 는 Baseline 이 아닙니다.

### 6.6 Baseline 학습 (공식: `baseline_v4`)

```bash
python scripts/06_train_baseline.py
```

- 조건은 스크립트 맨 위 `BASELINE` 한 곳에서만 정합니다 (YOLO11n · epoch 50 · imgsz 640 · batch 16 · seed 42 · AdamW · lr0 0.001).
- `data/yolo` 가 `kimchi_v4` 이고 train·val 이 manifest 와 정확히 같아야 시작합니다.
- 결과: `runs/baseline_v4/`, `models/baseline/baseline_best.pt`, `reports/baseline_training_condition.md`
- 이력: kimchi_v1 첫 Baseline 은 `runs/baseline_v1/`, `models/baseline/baseline_v1_best.pt`, `reports/baseline_v1_*` (실패 분석의 근거)

### 6.7 5일차 — Validation 평가 · 이미지 Detection

```bash
# Validation 132장 공식 평가 → reports/baseline_metrics.csv, Class 별 성능, 그래프
python scripts/07_evaluate_baseline.py

# 사진마다 예측을 정답과 나란히 그려 보기 → runs/predict/baseline_val_images/compare/
python scripts/08_predict_images.py
python scripts/08_predict_images.py --conf 0.5 --limit 10   # 기준을 바꿔 보기
```

- Frozen Test 사진은 두 스크립트 모두 막혀 있습니다 (8일차에 `--allow-test`).

### 6.8 6일차 — Failure Analysis

```bash
python scripts/09_collect_failures.py
```

- 결과: `reports/failure_analysis.csv` 외 요약 3개, `demo/failure_analysis/*.jpg`(대표 실패 사진, Git 제외)
- 원인 가설과 다음 실험: [`reports/failure_hypothesis.md`](reports/failure_hypothesis.md)

### 6.9 해상도 개선 실험 — exp001 (640 → 1280) · exp002 (1280 → 1920)

```bash
python scripts/10_train_v2.py               # exp001
python scripts/10_train_v2.py --exp exp002  # exp002 (batch 6 — 1920 메모리 한계, gradient 누적으로 갱신당 사진 수는 거의 같음)
```

- 공식 exp001 (`kimchi_v4`): Baseline(`baseline_v4`) 조건에서 imgsz 만 640 → 1280 → `runs/exp001_v4_imgsz1280/`, `models/improved/exp001_best.pt`, `reports/exp001_training_condition.md`
- 이력: 예비 실험 `runs/pilot_v1_imgsz1280/` (kimchi_v1, mAP50-95 0.351 → 0.519), 데이터 개선 과정 `runs/history_v2_imgsz1280/`·`history_v3_imgsz1280/` (Weight 는 `models/improved/history_*`)
- RTX 3060 batch 16 기준 GPU 약 9.2GB, 약 10~13분

### 6.10 Class 5(갈변) 라벨 재검수 → `kimchi_v3`

기준: [`docs/standards/class_guide.md`](../subject7/docs/standards/class_guide.md) Class 5 "검출 대상 범위" (2026-10-14 개정)

```bash
# 1) subject7/ 에서 라벨링 프로그램 실행 → [폴더 열기] 로 data/final 을 열고 작업 목록대로 고친 뒤 저장
cd ~/group_3/subject7 && ~/group_3/.venv/bin/python main.py

# 2) 고친 TXT 를 kimchi_v3 라벨 수정본으로 가져오기 (먼저 확인만, 그다음 --apply)
cd ~/group_3/subject8
.venv/bin/python scripts/04_import_label_fixes.py
.venv/bin/python scripts/04_import_label_fixes.py --apply

# 3) 데이터 만들기 → Baseline 학습 (v3 라벨은 kimchi_v4 도 같이 씀 — 지금 기본값은 kimchi_v4)
.venv/bin/python scripts/03_build_split.py --version kimchi_v4 --copy-files
.venv/bin/python scripts/10_train_v2.py
```

- 작업 목록: `reports/class5/class5_relabel_worklist.csv` (화면 번호 = 검수표 No, 라벨 목록 No = 원본 TXT 줄 번호, 위치 좌표 포함). 박스별 측정값·1차 판정: `reports/class5/class5_review.csv`, 확대 사진: `demo/label_review/class5/` (Git 제외)
- `data/final` 사진을 고치면 `data/work/_RAW밖/` 에만 저장되고 교과 7 작업본·검수표는 바뀌지 않습니다.

## 7. Dataset Split (`kimchi_v4` = `kimchi_v3` Class 5 개정 라벨 + G09 마지막 배치 Val, FROZEN)

- **정책**: 방안 B — 촬영 간격 5분 초과로 나눈 18개 `capture_group` 을 묶음 단위로 배정 + 예외 3건: `G00` 을 파/파+고추 구간별 시간순 블록으로 분할, `G12` 가운데 배치 25장을 Train 으로 (마른 잎·반점 갈변이 Train 에 있도록), `G09` 마지막 배치 25장을 Val 로 (Val 갈변 8 → 75개). Val 이 한 회차에 몰리지 않게 `G05` 를 통째로 Val 로
- 버전: `kimchi_v1`(2026-10-12) → `v2`(분할, H1·H2) → `v3`(Class 5 라벨 개정) → `v4`(G09 분할) — 이유는 [split_policy.md 7장](docs/split_policy.md). 버전마다 Val 이 달라 Validation 점수는 직접 비교하지 않습니다.
- 상세 근거·유사도 검증·예외 사유: [docs/split_policy.md](docs/split_policy.md)
- 과정 전체를 그림으로 정리한 문서: [docs/process/dataset_audit_and_split.md](docs/process/dataset_audit_and_split.md)
- Bridge Holdout 은 교과 8 학습·튜닝·모델 선택·Frozen Test 에 사용하지 않고 교과 14 용으로 보존합니다. `dataset.yaml` 에 넣지 않습니다.

| 역할 | 장수 | C0 | C1 | C2 | C3 | C5 | C6 | 용도 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Train | 526 | 161 | 352 | 188 | 82 | 43 | 29 | 모델 학습 (이물 단독 150장 포함) |
| Validation | 132 | 43 | 121 | 41 | 34 | 32 | 8 | Baseline vs Improved 비교 · Final 선택 |
| Frozen Test | 84 | 16 | 51 | 68 | 21 | 9 | 8 | Final Model 확정 후 마지막 평가 |
| Bridge Holdout | 158 | 65 | 72 | 75 | 60 | 13 | 9 | 교과 14 인계 |
| **합계** | **900** | 285 | 596 | 372 | 197 | 198 | 54 | |

*(숫자는 해당 Class BBox 가 1개 이상 있는 사진 수)*

산출물 1: `configs/dataset.yaml`, `manifests/split_manifest.csv`, `manifests/{train,val,test,bridge_holdout}.csv`, `docs/split_policy.md`, `reports/dataset_summary.csv`

## 8. Baseline (`baseline_v4` — kimchi_v4 · YOLO11n · imgsz 640)

- Smoke Test: ✅ 통과 (2026-10-14, `reports/history/smoke_test.md` — batch 16 에서 GPU 2.1GB)
- Baseline 학습: ✅ 완료 (2026-10-14, 50 epoch · 약 5분) — [`reports/baseline_training_condition.md`](reports/baseline_training_condition.md), `models/baseline/baseline_best.pt`, `runs/baseline_v4/results.csv`
- Validation 평가 (2026-10-14, 132장 · 정답 BBox 696개) — [`reports/baseline_metrics.csv`](reports/baseline_metrics.csv), [`reports/baseline_class_metrics.csv`](reports/baseline_class_metrics.csv)

| Precision | Recall | mAP50 | mAP50-95 |
|---:|---:|---:|---:|
| 0.835 | 0.675 | 0.764 | 0.538 |

| Class | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| 0 leaf_paper | 0.674 | 0.591 | 0.664 | 0.550 |
| 1 plastic_stone_metal | 0.900 | 0.586 | 0.755 | 0.519 |
| 2 branch | 0.662 | 0.641 | 0.664 | 0.521 |
| 3 insect | 0.825 | 0.750 | 0.812 | 0.464 |
| 4 rubber_glove_unused | - | - | - | - (Instance 0건) |
| 5 disease_browning | 0.982 | 0.738 | 0.831 | 0.536 |
| 6 green_onion_pepper | 0.968 | 0.743 | 0.857 | 0.640 |

- 그래프: `reports/figures/baseline/baseline_results.png`, `baseline_confusion_matrix.png`, `baseline_pr_curve.png`
- **이력 — 첫 Baseline `baseline_v1`** (kimchi_v1 · 640, Val 84장): P 0.432 · R 0.480 · mAP50 0.491 · mAP50-95 0.351 (`reports/baseline_v1_*`). 이 모델의 실패 분석(9장)으로 Dataset 을 v2~v4 로 고친 뒤, 같은 Version 에서 Baseline 을 다시 학습했습니다 (가이드 11.5·20.5). Val 이 달라 숫자를 직접 비교하지 않습니다.

## 9. Failure Analysis

상세: [`reports/failure_hypothesis.md`](reports/failure_hypothesis.md) · 근거 표 `reports/failure_*.csv`

모델은 이물의 **위치는 대체로 찾지만 종류를 틀립니다** (정답 515개 중 TP 191 · CLASS_ERROR 171 · FN 153).

| 가설 | 분류 | 핵심 근거 | 대응 |
|---|---|---|---|
| H1 Val 의 나뭇잎·갈변이 Train 과 모습이 다름 | DATA | Val 75/84장이 G12. 나뭇잎 Train=빨간 꽃잎·종이 / Val=마른 잎. 갈변 Train 181px 썩은 잎 / Val 57px 반점 | Split 기준 보강 검토 |
| H2 G00 시간순 분할로 고추가 Train 에 3개뿐 | SPLIT | Train 파 127·고추 3 / Val 고추 24 → 플라스틱으로 예측 | `kimchi_v2` 로 수정 + Baseline 재학습 |
| H3 같은 물체를 두 Class 로 예측 | INFERENCE | FP 180 중 93 | `agnostic_nms` 비교 (재학습 없음) |
| H4 작은 이물 놓침 | MODEL | 150px 미만 Recall: 나뭇가지 0.20 · 벌레 0.47 · 갈변 0 | `imgsz` 640 → 1280 |
| H5 정상 김치를 이물로 | DATA | 배경 FP 23 (녹색 잎끝·반투명 배추) | 한계로 기록 |

## 10. Improvement — exp001: imgsz 640 → 1280 (H4)

같은 `kimchi_v4` Val 132장, 나머지 조건 동일 (YOLO11n · epoch 50 · batch 16 · seed 42 · AdamW · lr0 0.001). 기록: [`reports/exp001_training_condition.md`](reports/exp001_training_condition.md), Weight `models/improved/exp001_best.pt`

| | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| Baseline v4 (640) | 0.835 | 0.675 | 0.764 | 0.538 |
| **exp001 (1280)** | **0.938** | **0.782** | **0.885** | **0.712** |
| exp002 (1920, batch 6) | 0.943 | 0.816 | 0.891 | 0.757 |
| exp003 (exp002 + epoch 100) | 0.929 | 0.815 | 0.913 | 0.774 |

| Class (mAP50-95) | Baseline | exp001 | exp002 | exp001 차이 | exp002 차이 (vs exp001) |
|---|---:|---:|---:|---:|---:|
| 0 leaf_paper | 0.550 | 0.728 | 0.755 | +0.177 | +0.027 |
| 1 plastic_stone_metal | 0.519 | 0.749 | 0.808 | +0.230 | +0.060 |
| 2 branch | 0.521 | 0.681 | 0.721 | +0.160 | +0.039 |
| 3 insect | 0.465 | 0.691 | 0.764 | +0.226 | +0.073 |
| 5 disease_browning | 0.536 | 0.651 | 0.653 | +0.116 | +0.002 |
| 6 green_onion_pepper | 0.640 | 0.773 | 0.838 | +0.133 | +0.065 |

- 갈변 (Val 75개, conf 0.25 · IoU 0.5): Baseline TP 60 · FN 15 · FP 5 → exp001 TP 63 · FN 12 · **FP 13** → exp002 TP 64 · FN 11 · FP 13 (놓침은 줄고 헛검출은 늘어남)
- exp002: 기록 [`reports/exp002_training_condition.md`](reports/exp002_training_condition.md), Weight `models/improved/exp002_best.pt`. 학습 22분 (exp001 10분), batch 6 은 1920 메모리 한계 때문 (gradient 누적으로 갱신당 사진 수 64 → 66장)
- exp003 (exp002 대비 epochs 50 → 100, `runs/exp003_v4_imgsz1920_epoch100`, 43분): mAP50-95 **+0.018** (기준 +0.02 미만), 모든 Class 소폭 상승 (나뭇잎 +0.035 · 갈변 +0.025 · 나뭇가지 +0.020). Val cls_loss 최저 0.510 @ epoch 78 (exp002 0.520 @ 48) 이후 0.532 로 다시 오름 → 78 epoch 이후 과적합 시작, best.pt 는 epoch 77. 놓친 박스 50 → 49 (갈변 11 → 8, 나뭇잎 7 → 9)
- 이력: 예비 실험 `pilot_v1_imgsz1280` (kimchi_v1), 데이터 개선 과정 `history_v2/v3_imgsz1280` — Val 이 달라 직접 비교하지 않음

## 11. Final Model

TBD (8일차) — Frozen Test 를 보기 전에 Validation 근거로 선택

## 12. Frozen Test

TBD (8일차)

## 13. Detection / Auto Label

TBD (8일차) — Auto Label 결과는 교과 7 라벨링 도구로 Human Review 후 확정

## 14. 알려진 한계

- 정상 김치(Negative) 이미지가 없습니다.
- Class 6 은 평가 역할마다 8~9장이고 같은 촬영 묶음(G00) 출신이라, 다른 Class 보다 성능이 좋게 나올 수 있습니다.
- 묶음 단위로 나눠 역할마다 Class 비율이 다릅니다. Val 과 Test 점수는 Class 별 결과와 함께 봅니다.
- **머리카락·실 등 Class 0~6 에 없는 이물은 검출 대상이 아닙니다.** 식품 이물로 중요하지만 회사 Class 정의에 없어 라벨을 그리지 않았습니다 (`kimchi_v3` 에서 머리카락을 나뭇가지로 그린 BBox 1개 삭제). 교과 14 에서 Class 추가 여부를 회사와 확인해야 합니다.
- **Class 5(갈변)**: 흩어진 점을 묶은 BBox·초록 잎맥·흐린 부분을 기준 개정으로 뺐습니다 (`kimchi_v3`). v3 에서 Val 갈변이 8개로 줄어 `kimchi_v4` 에서 G09 마지막 배치를 Val 로 보냈습니다 (Val 갈변 75개). 다만 Val 갈변의 대부분이 G09 한 회차 출신이라 Val 갈변 점수는 다소 낙관적일 수 있습니다. Frozen Test(갈변 16개)는 최종 모델 확정 후 한 번만 평가합니다. 작은 갈변(원본 짧은 변 20px 안팎)은 imgsz 1280 에서 3~5px 라 검출이 어렵습니다 (타일링 과제).
- 그 밖: TBD

## 15. 교과 14 Handoff

TBD (9일차) — `docs/handoff_subject14.md`

## 디렉토리 구조

```text
subject8/
├── .vscode/                        # 팀 공통 VSCode 설정 (인터프리터 · F5 실행 메뉴)
├── configs/dataset.yaml            # YOLO 학습용 Dataset 설정 (산출물 1)
├── data/                           # 사진(*.jpg)은 Git 제외, 라벨 TXT·검수표는 Git 에 있음
│   ├── subject7_final/             # 교과 7 FINAL: labels/ · 검수표.csv (Git) + images/ (각 PC 에 복사)
│   ├── label_fixes/kimchi_v3/      # kimchi_v3~ 라벨 수정본 TXT (Git)
│   ├── yolo/                       # 03 --copy-files 로 만든 train / val / test (Git 제외)
│   └── bridge_holdout/             # 03 --copy-files 로 만든 교과 14 보존용 (Git 제외)
├── docs/
│   ├── split_policy.md             # Split 정책서 (산출물 1)
│   └── process/                    # 과정 정리 (이해·포트폴리오용)
├── manifests/                      # split_manifest.csv + 역할별 CSV (산출물 1)
├── models/                         # 실험별 best Weight (Git) — baseline/, improved/, final/
├── runs/<실행>/                     # results.csv · args.yaml 만 Git (Ultralytics 원본은 Git 제외)
├── reports/
│   ├── figures/                    # 핵심 모델 그래프 + runs/ (실행별 학습 곡선) + runs_comparison_<Version>.png
│   ├── runs_summary.csv            # 실행별 조건과 best 지표
│   ├── audit_*.csv · leakage_check.csv · capture_group_summary.csv   # Data Audit (2일차)
│   ├── dataset_summary.csv         # 역할별 장수 (산출물 1)
│   ├── *_training_condition.md     # 학습 조건 기록 (산출물 2·4)
│   ├── baseline_*metrics.csv       # Validation 평가 (산출물 2)
│   └── failure_*                   # 실패 분석 (산출물 3)
├── scripts/                        # 01~10 일차별 실행 + plot_runs.py (그래프)
└── src/
    ├── constants.py                # Class·장면·Version 별 분할 규칙 (SSOT)
    ├── dataset_audit.py · leakage_check.py · split_builder.py · smoke_dataset.py
    ├── train_detector.py · evaluate_detector.py · inference.py · failure_analyzer.py
```
