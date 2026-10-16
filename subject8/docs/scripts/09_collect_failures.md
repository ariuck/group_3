# `subject8/scripts/09_collect_failures.py`

> 6일차 Failure Analysis. 모델이 Validation 에서 틀린 것을 모아 `failure_analysis.csv`(산출물 3)와 요약 표 3개, 대표 실패 사진 모음(`demo/failure_analysis/`)을 만든다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/09_collect_failures.py)

## 사용법

```bash
cd subject8
python scripts/09_collect_failures.py                                # 공식 Baseline → failure_*.csv
python scripts/09_collect_failures.py --model exp002_v5_imgsz1920    # 다른 모델 → exp002_v5_imgsz1920_failure_*.csv
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--model` | `baseline` | `baseline` · `final` · 실행 이름 · `.pt` 경로 ([`registry.resolve`](../src/registry.md)). 타일링 모델은 지원하지 않음 |
| `--conf` | 0.25 | 판정 기준 확신도 |
| `--imgsz` | 그 모델을 학습할 때의 값 | |
| `--prefix` | 공식 Baseline `failure`, 그 밖 `<실행>_failure` | 결과 파일 이름 앞부분. `failure` 가 아니면 사진 모음은 `demo/failure_analysis/<prefix>/` |

| 출력 (공식 Version → `reports/03_failure_analysis/`, 지난 Version → `reports/history/<Version>/03_failure_analysis/`) | 내용 |
|---|---|
| `<prefix>_analysis.csv` | 실패 1건 = 1줄 ([`collect_failures`](../src/failure_analyzer.md) 칸) |
| `<prefix>_summary.csv` | 실패 유형 × Class 개수 |
| `<prefix>_recall_by_size.csv` | Class × 크기 구간 Recall |
| `<prefix>_box_size_shift.csv` | Class 별 박스 크기 Train vs Val |
| `demo/failure_analysis/[<prefix>/]*.jpg` | 유형별 대표 실패 5장 (`fn`, `class_error`, `fp_duplicate`, `fp_partial`, `fp_background`) + Class 별 Train vs Val 비교 (Git 제외) |

콘솔: 유형별 건수, 유형×Class(5건 이상), 종류를 틀린 조합, 크기별 Recall, Train vs Val 박스 크기.

## 의존성

- **사용하는 것**: [`src/registry`](../src/registry.md), [`src/failure_analyzer`](../src/failure_analyzer.md), [`src/split_builder`](../src/split_builder.md) (그 Version 의 `yolo_dir`·`manifest_dir`), [`src/train_detector`](../src/train_detector.md) (`rel`)
- **사용하는 곳**: 직접 실행 (교과 8 6일차, 개선 모델 비교)

## 주의사항

- Validation 만 분석한다 (Frozen Test 사용 안 함).
- 원인 판단과 다음 실험은 이 스크립트가 아니라 `reports/03_failure_analysis/failure_hypothesis.md` 에 사람이 정리한다.
