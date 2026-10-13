# `subject8_kimchi_detection/scripts/02_audit_subject7_final.py`

> 교과 7 에서 넘겨받은 최종본(900장)을 점검해 수량·Class 분포·이미지별 BBox 수·장면 유형·Class×장면·출처·Data Leakage 를 콘솔에 보여 주고, 보고서 CSV 5개를 만든다. (가이드 2일차 15.1~15.3)

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/scripts/02_audit_subject7_final.py)

## 사용법

```bash
cd subject8_kimchi_detection
python scripts/02_audit_subject7_final.py
```

| 입력 | 출력 |
|---|---|
| `data/subject7_final/` (`images/`, `labels/`, `검수표.csv`) — 교과 7 [`build_final`](../../tools/build_final.md) 결과 | `reports/audit_issue.csv`, `reports/audit_summary.csv`, `reports/audit_class_scene.csv`, `reports/leakage_check.csv`, `reports/capture_group_summary.csv` |

콘솔 출력:

| 번호 | 내용 | 가이드 |
|---|---|---|
| [1] | 전체 수량 (이미지·라벨·빈 라벨·BBox·이슈) | 15.1 |
| [2] | Class 별 BBox 막대그래프 | 15.1 |
| [3] | 이미지별 BBox 수 (min·median·mean·max, 분포) | 15.1 |
| [4] | 이미지 유형 | 15.1 |
| [5] | Class × 이미지 유형 (Class 가 들어 있는 사진 수) | 15.2 |
| [6] | 출처 데이터셋과 원래 split | 15.1 |
| [7] | Data Leakage — 촬영 묶음 수, 완전 동일·거의 같은 사진 쌍(같은 묶음/다른 묶음), 평균 지문 거리, 원래 train/validation 이 섞인 묶음 수 | 15.3 |

다른 묶음 사이에 거의 같은 사진이 있으면 `[WARN]` 을 출력한다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `PROJECT_ROOT` | `subject8_kimchi_detection/` |
| `section(title)` | 콘솔 구분선 |
| `main()` | [`DatasetAuditor`](../src/dataset_audit.md) 실행 → [`SplitBuilder.assign_capture_groups`](../src/split_builder.md) 로 묶음 부여 → [`run_leakage_check`](../src/leakage_check.md) |

## 의존성

- **사용하는 것**: [`src/dataset_audit`](../src/dataset_audit.md) (`DatasetAuditor`, `CLASS_NAMES`, `SCENE_TYPES`), [`src/leakage_check`](../src/leakage_check.md), [`src/split_builder`](../src/split_builder.md) (`SplitBuilder`), `pandas`
- **사용하는 곳**: 직접 실행 (교과 8 2일차 데이터 점검)

## 주의사항

- `sys.path` 에 subject8 폴더를 추가해 `from src.dataset_audit import ...` 로 가져온다. 저장소 루트의 `src/`(교과 7 라벨링 프로그램)와 **패키지 이름이 같으므로**, 저장소 루트를 `sys.path` 앞쪽에 두고 실행하면(예: 루트에서 `python -m ...`) 엉뚱한 `src` 를 찾는다. 이 스크립트는 `python scripts/02_...py` 형태로 실행한다.
- `data/subject7_final/` 은 회사 데이터라 Git 에 없다. 교과 7 최종본을 이 위치에 복사해 두어야 한다.
- 실행할 때마다 `reports/` 의 CSV 5개를 덮어쓴다. 데이터가 같으면 내용도 같다.
