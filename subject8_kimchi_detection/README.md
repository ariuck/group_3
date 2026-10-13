# AI Campus Subject 8
# 조각김치 이물검출 Object Detection (YOLO11n)

교과 8 `[중간] Vision 기반 객체검출 모듈` 과제 저장소입니다.
교과 7 FINAL 검수 완료 4K 조각김치 데이터셋(900장)을 촬영 회차 누수를 막아 분할하고, YOLO11n 을 파인튜닝하여 교과 14 로 연결합니다.

> **진행 상태**: 3일차 — Dataset Split `kimchi_v1` FROZEN (2026-10-12)
>
> **데이터 성격**: AI캠퍼스 교육을 위해 실제 산업데이터와 유사한 분포 구조로 100% 가상 생성된 조각김치 이물검출 학습데이터를 사용합니다.
>
> **보안**: 이미지·라벨(`data/`)과 모델 Weight(`*.pt`), 학습 결과(`runs/`)는 `.gitignore` 로 제외합니다. 이미지는 Git 에 올리지 않습니다.
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
| QA 결과 | [QA Summary](../reports/qa_summary.md) — FAIL 0 · REVIEW 0 · **교과 8 사용 가능** |
| 인계 문서 | [교과 8 Handoff](../docs/handoff/subject08_handoff.md) |

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

Data Audit 결과 (`scripts/02_audit_subject7_final.py` → `reports/audit_summary.csv`, `reports/audit_issue.csv`):

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
| Python | 3.14.4 (`subject8_kimchi_detection/.venv`) |
| PyTorch | 2.14.1+cu130 |
| Ultralytics | 8.4.175 |
| CUDA available | True |
| `YOLO("yolo11n.pt")` Load | 성공 (COCO 80 Class, 2026-10-12 확인) |

## 6. 실행 및 재현 방법

모든 Script 는 이 폴더(`subject8_kimchi_detection/`)에서 실행합니다. `configs/dataset.yaml` 의 `path: data/yolo` 도 이 위치 기준입니다.

### 6.1 가상환경 · 의존성

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Python / PyTorch / Ultralytics / CUDA 확인 + YOLO11n Load
python scripts/01_check_environment.py
```

### 6.2 데이터 준비 (`data/subject7_final/`)

```bash
cp -r ../data/final data/subject7_final
```

평평한 구조(`images/`)와 교과 7 원본 구조(`images/train`, `images/validation`)를 모두 읽습니다.

### 6.3 2일차 — Data Audit

```bash
python scripts/02_audit_subject7_final.py
```

- 이미지-라벨 1:1 매칭, YOLO 좌표(0~1)·사진 밖 BBox, Class 범위(0~6), 이름 중복, 검수표 대조 전수 검사
- 이미지별 BBox 수, Class × 장면 분포 (가이드 15.1·15.2)
- 촬영 묶음(5분 간격) × 사진 지문(dHash)으로 Data Leakage 확인 (가이드 15.3)
- 산출물: `reports/audit_summary.csv`, `reports/audit_issue.csv`, `reports/audit_class_scene.csv`, `reports/leakage_check.csv`, `reports/capture_group_summary.csv`

시험 (가짜 데이터로 감사·누수 검사가 오류를 잡는지 확인):

```bash
python -m unittest discover -s tests -v
```

### 6.4 3일차 — Dataset Split & Freeze

```bash
# manifest · dataset.yaml · dataset_summary 생성
python scripts/03_build_split.py

# data/yolo/, data/bridge_holdout/ 실제 폴더까지 만들 때 (기존 폴더는 지우고 다시 만듦)
python scripts/03_build_split.py --copy-files
```

## 7. Dataset Split (`kimchi_v1`, FROZEN)

- **정책**: 방안 B — 촬영 간격 5분 초과로 나눈 18개 `capture_group` 을 묶음 단위로 배정 + Class 6 평가를 위해 `G00` 50장만 시간순 연속 블록으로 분할
- 상세 근거·유사도 검증·예외 사유: [docs/split_policy.md](docs/split_policy.md)
- 과정 전체를 그림으로 정리한 문서: [docs/process/dataset_audit_and_split.md](docs/process/dataset_audit_and_split.md)
- Bridge Holdout 은 교과 8 학습·튜닝·모델 선택·Frozen Test 에 사용하지 않고 교과 14 용으로 보존합니다. `dataset.yaml` 에 넣지 않습니다.

| 역할 | 장수 | C0 | C1 | C2 | C3 | C5 | C6 | 용도 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Train | 574 | 143 | 421 | 206 | 97 | 86 | 29 | 모델 학습 (이물 단독 150장 포함) |
| Validation | 84 | 61 | 52 | 24 | 19 | 44 | 8 | Baseline vs Improved 비교 · Final 선택 |
| Frozen Test | 84 | 16 | 51 | 67 | 21 | 25 | 8 | Final Model 확정 후 마지막 평가 |
| Bridge Holdout | 158 | 65 | 72 | 75 | 60 | 43 | 9 | 교과 14 인계 |
| **합계** | **900** | 285 | 596 | 372 | 197 | 198 | 54 | |

*(숫자는 해당 Class BBox 가 1개 이상 있는 사진 수)*

산출물 1: `configs/dataset.yaml`, `manifests/split_manifest.csv`, `manifests/{train,val,test,bridge_holdout}.csv`, `docs/split_policy.md`, `reports/dataset_summary.csv`

## 8. Baseline

TBD (4~5일차) — `reports/baseline_training_condition.md`, `models/baseline/baseline_best.pt`, `reports/baseline_metrics.csv`

## 9. Failure Analysis

TBD (6일차) — `reports/failure_analysis.csv`, `reports/failure_hypothesis.md`

## 10. Improvement

TBD (7일차) — 한 번에 주요 변수 하나만 변경, 같은 Validation 에서 비교

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
- 그 밖: TBD

## 15. 교과 14 Handoff

TBD (9일차) — `docs/handoff_subject14.md`

## 디렉토리 구조

```text
subject8_kimchi_detection/
├── configs/dataset.yaml            # YOLO 학습용 Dataset 설정 (산출물 1)
├── data/                           # Git 제외
│   ├── subject7_final/             # 교과 7 FINAL 복사본 (JPG, TXT, 검수표.csv)
│   ├── yolo/                       # --copy-files 로 만든 train / val / test
│   └── bridge_holdout/             # --copy-files 로 만든 교과 14 보존용
├── docs/
│   ├── split_policy.md             # Split 정책서 (산출물 1)
│   └── process/                    # 과정 정리 (이해·포트폴리오용)
├── manifests/                      # split_manifest.csv + 역할별 CSV (산출물 1)
├── reports/
│   ├── audit_summary.csv           # Data Audit 요약 (이미지별 BBox 수 포함)
│   ├── audit_issue.csv             # Data Audit 이슈 목록 (0건)
│   ├── audit_class_scene.csv       # Class × 장면 분포
│   ├── leakage_check.csv           # Data Leakage 지표 (dHash)
│   ├── capture_group_summary.csv   # 촬영 묶음 18개 요약
│   └── dataset_summary.csv         # 역할별 장수 (산출물 1)
├── scripts/
│   ├── 01_check_environment.py     # 환경 점검 + YOLO11n Load
│   ├── 02_audit_subject7_final.py  # Data Audit + Leakage 확인
│   └── 03_build_split.py           # Split · manifest · dataset.yaml 생성
├── src/
│   ├── dataset_audit.py            # Data Audit 기능
│   ├── leakage_check.py            # 사진 지문(dHash) 누수 확인
│   └── split_builder.py            # capture_group · Split 기능
└── tests/test_dataset_audit.py     # 감사·누수 검사 시험
```
