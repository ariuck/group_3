# `subject8/src/constants.py`

> 교과 8 전체가 함께 쓰는 상수의 유일한 정의 (SSOT). Class 이름, 장면 유형, 촬영 묶음 기준, Dataset Version 별 분할 규칙, 라벨 수정본 경로, 역할·용도를 한 곳에서만 고친다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../../subject8/src/constants.py)

## 역할

- 같은 값을 여러 파일에 복사해 두면 한쪽만 고쳐져 어긋난다. 분할·감사 코드는 모두 여기서 값을 가져온다.
- 혜성 `refactor(subject8): extract constants SSOT` 를 kimchi_v4 기준으로 확장했다 (2026-10-15 병합).

## 주요 구성요소

| 이름 | 값 / 뜻 |
|---|---|
| `CLASS_NAMES` | `{0: leaf_paper, 1: plastic_stone_metal, 2: branch, 3: insect, 4: rubber_glove_unused, 5: disease_browning, 6: green_onion_pepper}` — Class 4 미사용이지만 번호 유지 |
| `SCENE_TYPES`, `NORMAL_SCENE` | 검수표 `이미지 유형` → 영문 scene_type. `정상 김치` 는 빈 TXT 대조에 쓴다 |
| `CAPTURE_GROUP_INTERVAL_SECONDS` | `300` — 촬영 간격이 이보다 길면 다음 묶음 |
| `DEFAULT_DATASET_VERSION` | `kimchi_v4` — `03_build_split.py` 기본값 |
| `DATASET_VERSIONS` | `kimchi_v1` ~ `kimchi_v4` |
| `GROUP_ROLE_MAP` | 묶음 통째 배정 (kimchi_v1 기준). 블록 분할 묶음에는 쓰지 않는다 |
| `GROUP_ROLE_OVERRIDES` | Version 별로 바뀌는 묶음 (v2~v4: `G05 → val`) |
| `group_role_map(version)` | `GROUP_ROLE_MAP` + 그 Version 의 `GROUP_ROLE_OVERRIDES` |
| `BLOCK_RULES` | `{version: {묶음: [(시작, 끝(미포함), 역할), ...]}}` — 묶음 안을 시간순으로 나누는 예외 (G00 · G12 · G09). 표는 [`split_builder`](split_builder.md) |
| `LABEL_FIX_DIRS` | Version 별 라벨 수정본 폴더 (v3·v4 → `data/label_fixes/kimchi_v3`) |
| `ROLES`, `ROLE_PURPOSES` | 역할 순서 `train, val, test, bridge_holdout` 와 `dataset_summary.csv` 의 `purpose` |

## 의존성

- **사용하는 것**: 없음
- **사용하는 곳**: [`src/split_builder`](split_builder.md), [`src/dataset_audit`](dataset_audit.md), [`scripts/02_audit_subject7_final`](../scripts/02_audit_subject7_final.md), [`scripts/03_build_split`](../scripts/03_build_split.md)

## 주의사항

- **분할 규칙을 바꾸면 Dataset Version 을 새로 만든다.** 기존 Version 의 `BLOCK_RULES`·`GROUP_ROLE_OVERRIDES` 를 고치면 이전 분할을 재현할 수 없다 (`--version kimchi_v1` 이 `af78faf` 시점 manifest 와 같게 나오는지로 확인).
- 새 Version 을 추가할 때는 `DATASET_VERSIONS`, `GROUP_ROLE_OVERRIDES`, `BLOCK_RULES` (필요하면 `LABEL_FIX_DIRS`) 를 함께 채운다.
