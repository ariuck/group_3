# `subject8/manifests/kimchi_v5_draft/tools/crops.py`

> kimchi_v5 분석 2단계 — 모든 박스를 15% 여백을 두고 잘라 SIFT 특징점·색 히스토그램·64px 썸네일을 `crops.pkl` 로 저장한다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/crops.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/crops.py <작업폴더>
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/features.pkl` ([`features`](features.md)), `data/yolo` · `data/bridge_holdout` 사진 (절반 크기로 읽음) | `<작업폴더>/crops.pkl` — 박스마다 `img_idx, image, group, box, cls, wpx, hpx, pts, des, hist, thumb` |

## 주의사항

- 분석 기록 (kimchi_v5 C안 결정 과정). 다음 단계는 [`match`](match.md).
- 박스를 256px 로 키우거나 줄여 SIFT 를 400개까지 뽑는다. 여백에 김치 배경이 들어가 매칭에 영향을 줄 수 있다.
