# `subject8/src/leakage_check.py`

> 촬영 묶음(`capture_group`)이 실제로 "비슷한 사진 묶음"인지 사진 지문(dHash)으로 확인한다. 묶음 사이에 거의 같은 사진이 있으면 묶음 단위로 나눠도 누수가 생긴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../src/leakage_check.py)

## 역할

- 가이드 15.3 Data Leakage 확인의 근거를 숫자로 남긴다: 완전 동일 사진, 이름만 다른 동일 사진, 거의 같은 장면.
- [`split_builder`](split_builder.md) 의 시간 기준 묶음(5분 간격)이 실제 촬영 묶음과 맞는지 교차 검증한다 (가이드: "시간 문자열을 확인 없이 Session 이라고 단정하지 않는다").
- [`split_policy.md`](../split_policy.md) 2.2·2.3 의 숫자를 재현한다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `HASH_W, HASH_H` | `17, 16` → 256bit 지문 |
| `NEAR_DUP_THRESHOLD` | `10` — 이 거리 이하면 "거의 같은 사진" |
| `dhash(path)` | 사진을 17×16 흑백으로 줄여, 옆 픽셀보다 밝으면 1 → 256bit 정수. JPEG 는 `draft` 로 작게 디코딩해 빠르다 |
| `hamming(a, b)` | 두 지문의 다른 bit 수 (0~256) |
| `run_leakage_check(df, images_dir, report_dir, workers=None)` | 900장 지문 계산(프로세스 병렬) → 모든 쌍 비교 → CSV 2개 저장, 지표 dict 반환 |

### 지문 거리 읽는 법

| 거리 | 의미 |
|---:|---|
| 0 | 사실상 같은 사진 |
| ≤ 10 | 거의 같은 사진 |
| 100 안팎 | 다른 사진 |

### 출력 파일

| 파일 | 내용 |
|---|---|
| `reports/audit/leakage_check.csv` | `metric, value` — 사진 수, 묶음 수, 완전 동일 쌍, 거의 같은 쌍(같은 묶음 / 다른 묶음), 평균 거리(같은 묶음 / 다른 묶음), 가장 가까운 사진까지 거리 최솟값·중앙값 |
| `reports/audit/capture_group_summary.csv` | 묶음별 `images, date, start, end, scene, original_train, original_validation, near_dup_pairs, internal_median_distance` |

`df` 에는 `이미지 파일명`, `capture_group` 이 있어야 하고, `원래 split`·`이미지 유형` 이 있으면 묶음 표에 넣는다.

## 의존성

- **사용하는 것**: `Pillow`, `pandas`, `concurrent.futures`
- **사용하는 곳**: [`scripts/02_audit_subject7_final`](../scripts/02_audit_subject7_final.md)

## 주의사항

- dHash 는 사진 **전체**의 밝기 패턴 비교다. 좌우 반전·회전한 사진, 같은 실물 이물을 다른 배치로 다시 찍은 사진은 잡지 못한다.
- 배경이 같은 사진(예: 이물 단독 `G17`)은 내용이 달라도 거리가 가깝게 나온다. 그래서 같은 묶음 안의 "거의 같은 쌍"은 대부분 G17 이다.
- 모든 쌍(약 40만 쌍)을 비교하므로 사진 수가 크게 늘면 느려진다 (900장 기준 약 2초).
- 사진을 찾지 못하면 `FileNotFoundError` 로 멈춘다.
