# `subject8/manifests/kimchi_v5_draft/tools/search.py`

> 평가 역할 3개(Val·Test·Bridge)를 촬영 묶음 단위로 고르는 모든 조합 중, 평가 역할마다 Class 별 박스 기준을 채우면서 **Train 이 가장 큰** 조합을 찾는다. A·B·C안이 여기서 나왔다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/search.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/search.py
```

입력 없음 (묶음별 박스 수 `S` 가 코드에 들어 있음 — [`groups`](groups.md) 결과). 출력은 콘솔: 기준(c0~c3 15 · 갈변 15/12/10, 10/10)별 상위 6개 조합과 Train 장수.

## 핵심 동작

- G00 은 평가 역할마다 6장(파·고추 30박스) 고정, G09·G17·G16 과 G00 나머지는 Train 고정.
- 기준을 채우는 최소 조합만 남긴 뒤 서로 겹치지 않는 3개를 골라 평가 장수 합이 가장 작은 순으로 보여 준다.

## 주의사항

- 분석 기록. 결정한 C안은 [`kimchi_v5_split`](../../../project/kimchi_v5_split.md) 과 `src/constants.py` 의 `kimchi_v5` 에 있다.
