# `subject8/manifests/kimchi_v5_draft/tools/split_v5c.py`

> kimchi_v5 **C안(채택)** 배정과 검증 지표 — [`split_v5`](split_v5.md) 와 같고 `SESSION` 표만 다르다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/split_v5c.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/split_v5c.py <작업폴더>
```

출력: `<작업폴더>/kimchi_v5_split_c.csv`. C안: Train = A안 + G15 (558장) / Val G05·G13 / Test G07·G14 / Bridge G10·G11·G12, G00 은 구간마다 평가 역할 3장씩.

## 주의사항

- 분석 기록. 실제 분할은 이 CSV 가 아니라 `src/constants.py` 의 `kimchi_v5` 규칙으로 [`03_build_split`](../../../scripts/03_build_split.md) 이 만든다 — 사진 단위로 같음을 확인했다.
