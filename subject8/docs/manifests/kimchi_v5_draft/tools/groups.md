# `subject8/manifests/kimchi_v5_draft/tools/groups.py`

> 촬영 묶음별 Class 박스 수(갈변·파는 사진 수도) 표와, dHash 거리 기준별 거의 같은 사진 쌍 수(묶음을 넘는 쌍 포함)를 콘솔에 출력한다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/groups.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/groups.py <작업폴더>
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/features.pkl` | 콘솔만 — 묶음×Class 표, G17 안 dHash ≤ 10 쌍 수, 기준 10~50 별 쌍 수 |

## 주의사항

- 분석 기록. 여기서 정한 묶음별 박스 수가 [`search`](search.md) 의 `S` 표가 되었다. "dHash ≤ 40 쌍이 모두 같은 묶음" 확인도 여기서 했다.
