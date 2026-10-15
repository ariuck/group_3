# `subject8/src/smoke_dataset.py`

> Smoke Test 용 작은 Dataset(Train 40 / Val 8)을 `data/yolo` 에서 뽑아 `data/smoke` 에 만들고 `configs/smoke_dataset.yaml` 을 쓴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../src/smoke_dataset.py)

## 역할

- 가이드 16.5 "Smoke Test 용 작은 Dataset" 구현. 성능이 아니라 학습 Pipeline 이 끝까지 도는지 보기 위한 데이터다.
- **Frozen Test 와 Bridge Holdout 은 쓰지 않는다** (train·val 에서만 뽑음).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `build_smoke_dataset(project_root, n_train=40, n_val=8, seed=42)` | `data/yolo/images/{train,val}` 에서 seed 고정 무작위 추출 → 사진·라벨을 `data/smoke/` 로 복사 → `configs/smoke_dataset.yaml` 작성. 반환: `yaml, root, train, val` |

- `data/smoke/` 는 실행할 때마다 지우고 새로 만든다 (이전 파일이 섞이지 않게). seed 가 같으면 같은 사진이 뽑힌다.
- Class 이름은 `configs/dataset.yaml` 의 `names` 를 그대로 복사한다 (Class ID 0~6 유지).

## 의존성

- **사용하는 것**: `PyYAML`
- **사용하는 곳**: [`scripts/05_smoke_train`](../scripts/05_smoke_train.md)

## 주의사항

- 먼저 `python scripts/03_build_split.py --copy-files` 로 `data/yolo` 가 있어야 한다.
- 무작위 추출이라 일부 Class 가 Smoke Val 8장에 없을 수 있다 (Smoke 목적상 문제없음).
