# `subject8/manifests/kimchi_v5_draft/tools/split_v5b.py`

> kimchi_v5 **B안** 배정과 검증 지표 — [`split_v5`](split_v5.md) 와 같고 `SESSION` 표만 다르다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/split_v5b.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/split_v5b.py <작업폴더>
```

출력: `<작업폴더>/kimchi_v5_split_b.csv`. B안: Train = A안 + G10·G15 (608장) / Val G11·G12 / Test G07·G14 / Bridge G05·G13.

## 주의사항

- 분석 기록. Val 갈변이 13박스로 기준(15)에 못 미쳐 채택하지 않았다.
