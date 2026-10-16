# `subject8/manifests/kimchi_v5_draft/tools/match.py`

> kimchi_v5 분석 3단계 — 같은 Class 박스끼리 "같은 실물인가" 를 SIFT 로 찾는다. GPU 로 후보를 고른 뒤 ratio test + RANSAC inlier 수로 확인한다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/match.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/match.py <작업폴더>
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/crops.pkl` ([`crops`](crops.md)) | `<작업폴더>/pairs.csv` — `cls, a, b, good, inliers, score, hist, img_a, img_b, ga, gb` |

## 핵심 동작

- 박스마다 같은 Class 의 다른 박스 중 유사도 0.90 이상 특징점이 많은 상위 12개를 후보로 고른다 (CUDA 필요).
- 같은 사진 안의 다른 박스 쌍(= 확실히 다른 물체)도 항상 계산해 기준 분포로 쓴다.

## 주의사항

- 분석 기록. **육안 확인 결과 묶음 사이의 강한 매칭(inlier ≥ 20)은 대부분 다른 물체였다** (마른 잎↔꽃잎, 굵은 가지↔솔잎). 그래서 [`kimchi_v5_split`](../../../project/kimchi_v5_split.md) 에서는 이 결과를 후보안 비교에 쓰지 않는다.
