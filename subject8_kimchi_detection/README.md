# Subject 8 — 조각김치 이물검출 YOLO11n 모듈

교과 8 `[중간] Vision 기반 객체검출 모듈` 과제 저장소입니다.  
교과 7 FINAL 검수 완료 4K 조각김치 데이터셋(900장)을 기반으로 회차(촬영 세션) 누수를 차단한 데이터 분할을 수행하고, YOLO11n 모델을 파인튜닝하여 교과 14 실전 배포 파이프라인으로 연결합니다.

---

## 📁 디렉토리 구조

```text
subject8_kimchi_detection/
├── configs/
│   └── dataset.yaml                # YOLO11 학습용 데이터셋 설정
├── data/
│   ├── subject7_final/             # 교과 7 최종 데이터셋 원본 (900장 JPG, TXT, 검수표.csv)
│   ├── yolo/                       # [옵션] 물리 배치된 YOLO 데이터셋 (train, val, test)
│   └── bridge_holdout/             # [옵션] 교과 14 인계용 물리 데이터셋
├── docs/
│   └── split_policy.md             # Dataset Split 정책서 (kimchi_v1 FROZEN)
├── manifests/
│   ├── split_manifest.csv          # 전체 900장 분할 메타데이터 (dataset_version 포함)
│   ├── train.csv                   # Train 574장 매니페스트
│   ├── val.csv                     # Validation 84장 매니페스트
│   ├── test.csv                    # Frozen Test 84장 매니페스트
│   └── bridge_holdout.csv          # Bridge Holdout 158장 매니페스트
├── reports/
│   ├── audit_summary.csv           # 900장 데이터 무결성 전수 감사 요약 통계
│   ├── audit_issue.csv             # 데이터 무결성 검사 이슈 목록 (0건 무결)
│   └── dataset_summary.csv         # 산출물 1 표준 양식 (role별 장수 및 용도)
├── scripts/
│   ├── 01_check_environment.py     # 환경(CUDA, PyTorch, YOLO11n) 점검
│   ├── 02_audit_subject7_final.py  # 900장 데이터 전수 무결성 검사 실행
│   └── 03_build_split.py           # Plan B 분할 및 매니페스트/설정/요약 생성
└── src/
    ├── dataset_audit.py            # 데이터 감사 핵심 모듈
    └── split_builder.py            # 촬영 묶음 분석 및 분할 빌더 모듈
```

---

## 🛠️ 실행 및 재현 방법

### 1. 가상환경 및 의존성 확인
```bash
# 가상환경 활성화 (Python 3.10+ / PyTorch / Ultralytics)
source .venv/bin/activate

# 환경 점검 및 YOLO11n 로드 확인
python scripts/01_check_environment.py
```

### 2. 데이터셋 준비 (`data/subject7_final/`)
교과 7 FINAL 산출물을 `data/subject7_final/` 경로에 배치합니다.  
단일 폴더 구조는 물론, 교과 7 원본 구조(`images/train`, `images/validation`)도 `rglob`으로 자동 감지하여 지원합니다.
```bash
# 디렉토리 구조 예시:
# data/subject7_final/
# ├── 검수표.csv
# ├── images/ (또는 하위 train/, validation/)
# └── labels/ (또는 하위 train/, validation/)
```

### 3. 2일차: 900장 데이터 전수 무결성 감사 (Audit)
```bash
python scripts/02_audit_subject7_final.py
```
- 이미지-라벨 1:1 매칭, YOLO BBox 정규화 좌표(0~1), Class 범위(0~6) 전수 검사
- 산출물: `reports/audit_summary.csv`, `reports/audit_issue.csv`

### 4. 3일차: 데이터셋 분할 (Dataset Split & Freeze)
```bash
# 메니페스트, YAML, 요약 통계 생성
python scripts/03_build_split.py

# 물리 디렉토리(data/yolo/, data/bridge_holdout/)까지 복사하려면 --copy-files 플래그 추가
python scripts/03_build_split.py --copy-files
```
- **정책**: 방안 B (18개 `capture_group` 세션 묶음 배정 + Class 6 희귀 클래스 평가를 위한 `G00` 50장 시간순 연속 블록 분할)
- **Dataset Version**: `kimchi_v1` (`FROZEN`)
- 산출물:
  - `manifests/split_manifest.csv` (전체 900장)
  - `manifests/train.csv` (574장), `val.csv` (84장), `test.csv` (84장), `bridge_holdout.csv` (158장)
  - `configs/dataset.yaml`
  - `reports/dataset_summary.csv` (가이드 산출물 1 표준 양식)

---

## 📊 Dataset Split 요약 (`kimchi_v1`)

| 역할 (Role) | 장수 | C0 (나뭇잎) | C1 (플라스틱) | C2 (나뭇가지) | C3 (벌레) | C5 (갈변) | C6 (파·고추) | 주요 용도 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Train** | **574장** | 143 | 421 | 206 | 97 | 86 | 29 | 모델 학습용 (이물 단독 150장 포함) |
| **Validation** | **84장** | 61 | 52 | 24 | 19 | 44 | 8 | 하이퍼파라미터 튜닝 및 모델 선택 |
| **Frozen Test** | **84장** | 16 | 51 | 67 | 21 | 25 | 8 | 최종 성능 검증 및 보고 (동결) |
| **Bridge Holdout** | **158장** | 65 | 72 | 75 | 60 | 43 | 9 | 교과 14 컨베이어 이물검출 실전 평가용 인계 |
| **전체 합계** | **900장** | 285 | 596 | 372 | 197 | 198 | 54 | 18개 묶음 전량 수용 |

상세한 분할 근거와 유사도 검증 결과는 [split_policy.md](file:///home/user1/group_3/subject8_kimchi_detection/docs/split_policy.md)를 참고하세요.
