# `subject8/manifests/kimchi_v5_draft/tools/features.py`

> kimchi_v5 분석 1단계 — `kimchi_v4` 900장의 특징(시각·묶음·박스·dHash·색 히스토그램·작은 사진·밝기)을 `features.pkl` 로 저장한다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/features.py)

## 사용법

```bash
cd subject8
python manifests/kimchi_v5_draft/tools/features.py <작업폴더>/features.pkl
```

| 입력 | 출력 |
|---|---|
| `manifests/split_manifest.csv` (v4), `data/yolo/` · `data/bridge_holdout/` 의 사진·라벨 | `<작업폴더>/features.pkl` — 시간순 900행 (`image, ts, group, old_split, scene, orig_split, boxes, dhash, hist, small, bright, contrast, shape`) |

## 주의사항

- kimchi_v5 C안을 고를 때 쓴 **분석 기록**이다. 결과는 [`kimchi_v5_split`](../../../project/kimchi_v5_split.md), 실제 분할은 `src/constants.py` 와 `manifests/kimchi_v5/` 에 있다.
- `data/yolo` (v4) 가 있어야 돌아간다. 다른 분석 스크립트(`crops`·`batches`·`split_v5*` 등)는 이 `features.pkl` 이 있는 폴더를 인자로 받는다.
