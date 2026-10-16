# `subject8/scripts/make_split_worksheet.py`

> 수동 분할(`kimchi_v5`) 준비. 6명이 나눠 볼 담당자별 작업 시트(CSV)와, 촬영 순서대로 썸네일을 깔고 정답 박스를 그린 확인용 사진판(JPG)을 만든다. 작업 방법은 [manual_split_guide](../project/manual_split_guide.md).

[← 코드 문서 목차](../README.md) · [코드 보기](../../scripts/make_split_worksheet.py)

## 사용법

```bash
cd subject8
python scripts/make_split_worksheet.py              # 작업 시트 6개 + 사진판 18장 (약 25초)
python scripts/make_split_worksheet.py --no-sheets  # 작업 시트만 (사진이 없는 PC)
```

| 입력 | 출력 |
|---|---|
| `subject7/data/final/검수표.csv`·`labels/`, 사진 `subject7/data/raw/`, 라벨 수정본 `data/label_fixes/kimchi_v3/` (`kimchi_v4` 라벨) | `manifests/manual_split/worksheet_<A~F>.csv` (Git), `demo/manual_split/<담당>_<촬영묶음>.jpg` (Git 제외) |

### 작업 시트 칸

`no`(전체 촬영 순서 1~900), `image`, `capture_group`, `date`, `time`, `gap_sec`(앞 사진과의 간격, 촬영 묶음 첫 장은 0), `n_boxes`, `classes`(`Class:개수`), `scene`, `assignee`, `reviewer`, 채울 칸 `batch_id`, `same_object_as`, `note`, `review_ok`, `review_note`

기존 Split(train/val/…)과 모델 성능은 **일부러 넣지 않는다** — 배치는 사진만 보고 정하기 위해서.

### 사진판

- 촬영 순서대로 6열. 각 썸네일 위 띠: `#번호 시각 +간격s Class:개수`
- 앞 사진과 **120초 이상** 끊긴 사진은 띠가 빨간색 (새 배치 후보, `GAP_HINT_SEC`)
- 정답 박스는 Class 색 ([`inference.COLORS`](../src/inference.md))

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `LABEL_VERSION` | `kimchi_v4` — 라벨은 그대로 쓰고 분할만 다시 정한다 |
| `ASSIGNEES` | 담당 A~F ↔ 촬영 묶음 (A: G00~G04 · B: G05~G06 · C: G07~G09 · D: G10~G12 · E: G13~G15 · F: G16~G17) |
| `REVIEWER` | 교차 확인 짝 A↔B · C↔D · E↔F |
| `collect(builder)` | 검수표 + 촬영 묶음 + (수정본 우선) 라벨 → 촬영 순서 표 |
| `write_sheets(df)` | 담당자별 CSV. **이미 있으면 덮어쓰지 않는다** (작성 중 보호) |
| `write_contact_sheets(df)` | 촬영 묶음별 사진판. JPEG 를 1/8 크기로 읽어 빠르다 |

## 의존성

- **사용하는 것**: [`src/split_builder`](../src/split_builder.md) (`assign_capture_groups`, `label_fix_dir`), [`src/inference`](../src/inference.md) (`load_gt`, `COLORS`), [`src/constants`](../src/constants.md), `opencv-python`, `pandas`
- **사용하는 곳**: 직접 실행 (수동 분할 1단계 준비)

## 주의사항

- 사진판은 회사 사진이라 `demo/` 에만 저장한다 (`.gitignore` 의 `*.jpg`). 각자 PC 에서 같은 명령으로 만든다.
- 담당 배정을 바꾸려면 `ASSIGNEES` 를 고치고, 이미 만든 `worksheet_*.csv` 를 지운 뒤 다시 실행한다.
