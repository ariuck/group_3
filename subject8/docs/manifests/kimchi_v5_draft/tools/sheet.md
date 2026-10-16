# `subject8/manifests/kimchi_v5_draft/tools/sheet.py`

> [`match`](match.md) 매칭을 눈으로 확인하는 사진판 — 묶음 사이 강매칭 예시(묶음쌍마다 중간 세기 1개, 최대 40개)와, 같은 사진 안 다른 박스인데 inlier 가 높은 기준 예시 10개.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/sheet.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/sheet.py <작업폴더>
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/crops.pkl`, `strong_pairs.csv`, `pairs.csv` | `<작업폴더>/sheet_cross.jpg`, `sheet_sameimg.jpg` (김치 사진이라 Git 에 올리지 않음) |

## 주의사항

- 분석 기록. 썸네일이 64px 라 다른 물체끼리 매칭된 것을 알아보기 어렵다 — 큰 crop 으로 다시 확인하니 대부분 다른 물체였다.
