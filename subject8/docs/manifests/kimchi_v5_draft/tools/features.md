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

## 분석 스크립트 실행 순서 (12개 전체)

`03_build_split.py --copy-files` 로 `data/yolo` (v4) 를 먼저 만든 뒤, 같은 작업폴더를 넘기며 차례로 실행한다.

```bash
W=~/kimchi_v5_work && mkdir -p $W     # /tmp 은 WSL 에서 메모리라 쓰지 않는다 && T=manifests/kimchi_v5_draft/tools
python $T/features.py $W/features.pkl   # 1. 사진 900장 특징
python $T/crops.py $W                   # 2. 박스 잘라내기 + SIFT
python $T/match.py $W                   # 3. 같은 물체 찾기 (GPU 필요)
python $T/batches.py $W                 # 4. 배치 자동 추정
python $T/anal_pairs.py $W              # 5. 매칭 정리 → strong_pairs.csv
python $T/split_v5c.py $W               # 6. C안 배정 + 검증 지표 (split_v5 = A안, split_v5b = B안)
python $T/search.py                     # 따로: A·B·C안 후보 찾기 (입력 없음)
python $T/groups.py $W; python $T/seq.py $W; python $T/sheet.py $W   # 확인용 표·사진판
```

이 순서는 분석을 **다시 해 볼 때만** 쓴다. 실제 분할은 `python scripts/03_build_split.py --version kimchi_v5 --copy-files` 한 줄로 만든다.

## 주의사항

- kimchi_v5 C안을 고를 때 쓴 **분석 기록**이다. 결과는 [`kimchi_v5_split`](../../../project/kimchi_v5_split.md), 실제 분할은 `src/constants.py` 와 `manifests/kimchi_v5/` 에 있다.
- `data/yolo` (v4) 가 있어야 돌아간다. 다른 분석 스크립트(`crops`·`batches`·`split_v5*` 등)는 이 `features.pkl` 이 있는 폴더를 인자로 받는다.
