# `subject8_kimchi_detection/scripts/02_audit_subject7_final.py`

> 교과 7 에서 넘겨받은 최종본(900장)을 점검해 수량·Class 분포·이미지 유형·출처를 콘솔에 보여 주고, 보고서 CSV 2개를 만든다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/scripts/02_audit_subject7_final.py)

## 사용법

```bash
cd subject8_kimchi_detection
python scripts/02_audit_subject7_final.py
```

| 입력 | 출력 |
|---|---|
| `data/subject7_final/` (`images/`, `labels/`, `검수표.csv`) — 교과 7 [`build_final`](../../tools/build_final.md) 결과 | `reports/audit_issue.csv`, `reports/audit_summary.csv` |

콘솔 출력: [1] 전체 수량(이미지·라벨·빈 라벨·BBox·이슈) · [2] Class 별 BBox 막대그래프 · [3] 이미지 유형 · [4] 출처 데이터셋과 원래 split

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `PROJECT_ROOT` | `subject8_kimchi_detection/` |
| `main()` | [`DatasetAuditor`](../src/dataset_audit.md) 실행 후 결과를 표로 출력 |

## 의존성

- **사용하는 것**: [`subject8 src/dataset_audit`](../src/dataset_audit.md) (`DatasetAuditor`, `CLASS_NAMES`)
- **사용하는 곳**: 직접 실행 (교과 8 2일차 데이터 점검)

## 주의사항

- `sys.path` 에 subject8 폴더를 추가해 `from src.dataset_audit import ...` 로 가져온다. 저장소 루트의 `src/`(교과 7 라벨링 프로그램)와 **패키지 이름이 같으므로**, 저장소 루트를 `sys.path` 앞쪽에 두고 실행하면(예: 루트에서 `python -m ...`) 엉뚱한 `src` 를 찾는다. 이 스크립트는 `python scripts/02_...py` 형태로 실행한다.
- `data/subject7_final/` 은 회사 데이터라 Git 에 없다. 교과 7 최종본을 이 위치에 복사해 두어야 한다.
