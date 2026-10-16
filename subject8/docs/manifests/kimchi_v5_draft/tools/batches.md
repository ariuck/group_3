# `subject8/manifests/kimchi_v5_draft/tools/batches.py`

> 촬영 묶음 안의 배치(같은 이물 세트를 위치만 바꿔 찍은 연속 사진) 경계를 박스 Class 구성으로 자동 추정해 `batches.csv` 를 만든다.

[← 코드 문서 목차](../../../README.md) · [코드 보기](../../../../manifests/kimchi_v5_draft/tools/batches.py)

## 사용법

```bash
python manifests/kimchi_v5_draft/tools/batches.py <작업폴더>
```

| 입력 | 출력 |
|---|---|
| `<작업폴더>/features.pkl`, G12 는 `manifests/manual_split/worksheet_D.csv` 의 `batch_id` | `<작업폴더>/batches.csv` — `image, group, batch, rule` (110배치) |

## 핵심 동작

- 구성(Class 집합, 1개짜리 덤 이물·소량 갈변·파는 무시)이 2장 이상 이어서 바뀌면 끊고, 매 장 바뀌는 구간은 `mixed-pool` 한 배치로 묶는다.

## 주의사항

- 분석 기록. 구성이 같은 다른 물체 세트를 구분하지 못해 실제 배치와 다르다 (예: G00 을 1배치로 봄). 기록용 배치는 육안 판정 70배치(`manifests/manual_split/`) 를 쓴다.
