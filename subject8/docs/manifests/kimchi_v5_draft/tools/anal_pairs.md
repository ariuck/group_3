# `subject8/manifests/kimchi_v5_draft/tools/anal_pairs.py`

> kimchi_v5 분석 4단계 — [`match`](match.md) 결과에 배치 이름을 붙이고, inlier 기준별로 같은 배치·같은 묶음·다른 묶음 매칭 수를 세어 `strong_pairs.csv` 를 만든다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/anal_pairs.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/anal_pairs.py <작업폴더> [inlier 기준, 기본 15]
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/pairs.csv`, `batches.csv`, `features.pkl` | `<작업폴더>/strong_pairs.csv` (+ `ba`, `bb` 배치 칸), 콘솔에 분위수·기준별 개수·Class×묶음쌍 표 |

## 주의사항

- 분석 기록. 저장소의 `manifests/kimchi_v5_draft/strong_pairs.csv` 가 이 결과다 (같은 사진 안 쌍은 빠짐). 오탐이 많아 근거로 쓰지 않는다 ([`match`](match.md) 주의사항).
- [`batches`](batches.md) 를 먼저 돌려야 한다.
