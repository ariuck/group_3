# `subject8_kimchi_detection/src/split_builder.py`

> 교과 8 데이터 분할기 `SplitBuilder`. 파일명 시각으로 촬영 묶음(Capture Group)을 만들고, **묶음 단위**로 train / val / test / bridge_holdout 을 배정해 같은 장면이 학습과 평가에 섞이지 않게 한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/src/split_builder.py)

## 역할

- 비슷한 시각에 찍은 사진은 거의 같은 장면이므로, 사진 단위로 무작위 분할하면 평가 점수가 부풀려진다(데이터 누수). 이를 막기 위해 시간 묶음 단위로 나눈다.
- 분할 결과를 Manifest·YOLO 설정·요약 보고서로 남기고, 원하면 실제 YOLO 폴더 구조를 만든다.

## 분할 방안 B (`assign_splits`)

| 묶음 | 역할 |
|---|---|
| G00 (50장) | 시간순 연속 블록: 앞 26장 train · 8장 val · 8장 test · 8장 bridge_holdout |
| G01, G12 | val |
| G07, G14 | test |
| G10, G13, G15 | bridge_holdout |
| G17 (150장, 이물 단독) | train |
| 나머지 (G02~G06, G08, G09, G11, G16) | train |

`bridge_holdout` 은 교과 14 연계용으로 따로 떼어 두는 사진이다 (`purpose = subject14_bridge`).

## 주요 구성요소

| 메서드 | 설명 |
|---|---|
| `SplitBuilder(project_root)` | 입력 `data/subject7_final/` (`검수표.csv`, `images/`, `labels/`), 출력 `manifests/`, `data/yolo/`, `data/bridge_holdout/`, `configs/`, `reports/` |
| `_find_file(base_dir, filename)` | 바로 아래에 없으면 하위 폴더를 뒤져 **처음 찾은 것** |
| `assign_capture_groups(df)` | 파일명 앞 `YYMMDD_HHMMSS` 를 시각으로 읽어 정렬, **300초 넘게** 벌어지면 다음 묶음. `capture_group` 열 추가 |
| `assign_splits(df, dataset_version="kimchi_v1")` | 묶음 수 18 · G00 50장 · G17 150장을 `assert` 로 확인 후 위 표대로 배정. `split`, `dataset_version` 열 추가 |
| `generate_manifests(df)` | `manifests/split_manifest.csv` + 역할별 CSV 4개 (UTF-8 BOM) |
| `generate_dataset_summary(df, dataset_version)` | `reports/dataset_summary.csv`: `dataset_version, role, image_count, purpose` |
| `build_physical_dataset(df, clean=True)` | `data/yolo/images|labels/{train,val,test}/`, `data/bridge_holdout/images|labels/` 에 복사 (이미 있는 파일은 건너뜀) |
| `generate_dataset_yaml()` | `configs/dataset.yaml` — `path: data/yolo`, train/val/test, Class 이름 0~6 |

## 의존성

- **사용하는 것**: `pandas`, `shutil`, `re`, `datetime`
- **사용하는 곳**: [`scripts/03_build_split`](../scripts/03_build_split.md)

## 주의사항

- **이 데이터셋 전용이다.** 묶음 수·G00·G17 장수와 묶음별 역할이 코드에 고정되어 있어, 데이터가 바뀌면 `assert` 에서 멈춘다. 다른 데이터에 쓰려면 `group_role_map` 과 검사값을 고쳐야 한다.
- 파일명이 `YYMMDD_HHMMSS` 로 시작하지 않으면 시각을 `datetime.min` 으로 둔다. 그런 사진이 있으면 모두 맨 앞 묶음(G00)으로 몰린다.
- `build_physical_dataset(clean=True)` 는 `data/yolo`, `data/bridge_holdout` 을 **`shutil.rmtree` 로 지운 뒤** 다시 만든다.
- `_find_file` 은 같은 이름이 여러 하위 폴더에 있으면 처음 찾은 것을 쓴다. 교과 7 최종본은 이름이 겹치지 않아 문제없다.
- `dataset_summary.csv` 만 BOM 없는 UTF-8 로 저장한다 (엑셀에서 한글이 깨져 보일 수 있으나 내용은 영문).
- `dataset.yaml` 의 `path: data/yolo` 는 상대 경로다. 학습은 `subject8_kimchi_detection/` 에서 실행해야 한다.
