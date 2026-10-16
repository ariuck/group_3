# `subject8/manifests/kimchi_v5_draft/tools/split_v5.py`

> kimchi_v5 **A안** 배정(묶음 통째 + G00 블록)을 만들고 v4 와 함께 검증 지표(역할별 장수·Class 박스·같은 묶음 출신 수·dHash 교차·실물 강매칭 비율)를 출력한다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/split_v5.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/split_v5.py <작업폴더>
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/features.pkl`, `batches.csv`, `pairs.csv`, `crops.pkl` | `<작업폴더>/kimchi_v5_split.csv` (`image, group, batch, old_split, split`) |

A안: Train G01~04·G06·G08·G09·G16·G17 / Val G07·G11·G12 / Test G05·G14 / Bridge G10·G13·G15.

## 주의사항

- 분석 기록. 같은 구조의 [`split_v5b`](split_v5b.md)(B안) · [`split_v5c`](split_v5c.md)(C안, 채택)와 `SESSION` 표만 다르다.
