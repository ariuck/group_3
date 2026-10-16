# `subject8/scripts/09_collect_failures.py`

> 6일차 Failure Analysis. Weight 가 Validation 에서 틀린 것을 모아 `reports/03_failure_analysis/failure_analysis.csv`(산출물 3)와 요약 표 3개, 대표 실패 사진 모음(`demo/failure_analysis/`)을 만든다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/09_collect_failures.py)

## 사용법

```bash
cd subject8
python scripts/09_collect_failures.py                                   # Baseline
python scripts/09_collect_failures.py --weights models/improved/exp001_best.pt --prefix exp001_failure   # 개선 모델
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--weights` | `models/baseline/baseline_best.pt` | |
| `--conf` | 0.25 | 판정 기준 확신도 |
| `--imgsz` | 640 | 학습 때와 같은 값 |
| `--prefix` | `failure` | 결과 파일 이름 앞부분. `failure` 가 아니면 사진 모음은 `demo/failure_analysis/<prefix>/` |

| 출력 | 내용 |
|---|---|
| `reports/<prefix>_analysis.csv` | 실패 1건 = 1줄 ([`collect_failures`](../src/failure_analyzer.md) 칸) |
| `reports/<prefix>_summary.csv` | 실패 유형 × Class 개수 |
| `reports/<prefix>_recall_by_size.csv` | Class × 크기 구간 Recall |
| `reports/<prefix>_box_size_shift.csv` | Class 별 박스 크기 Train vs Val |
| `demo/failure_analysis/*.jpg` | 유형별 대표 실패 5장 (`fn`, `class_error`, `fp_duplicate`, `fp_partial`, `fp_background`) + Class 별 Train vs Val 비교 |

콘솔: 유형별 건수, 유형×Class(5건 이상), 종류를 틀린 조합, 크기별 Recall, Train vs Val 박스 크기.

## 의존성

- **사용하는 것**: [`src/failure_analyzer`](../src/failure_analyzer.md), [`src/train_detector`](../src/train_detector.md) (`rel`), `manifests/split_manifest.csv`(capture_group·scene_type)
- **사용하는 곳**: 직접 실행 (교과 8 6일차, 7일차 개선 모델 비교)

## 주의사항

- Validation 만 분석한다 (Frozen Test 사용 안 함).
- 원인 판단과 다음 실험은 이 스크립트가 아니라 `reports/03_failure_analysis/failure_hypothesis.md` 에 사람이 정리한다.
