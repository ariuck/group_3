# `src/manifest/manifest_writer.py`

> 검수표(Manifest) CSV 기록. [저장]할 때 자동 칸을 채우고, 입력칸(검수 기록)에서 받은 사람 칸을 함께 기록한다. 상태 자동 결정 규칙이 여기에 있다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../src/manifest/manifest_writer.py)

## 역할

- 파일: `manifests/dataset_manifest.csv` — 칸 19개. `dataset_manifest.xlsx` 검수표 틀과 같은 머리글이다. 기준 문서: [standards/manifest_guide](../../../standards/manifest_guide.md)
- 같은 사진을 다시 저장하면 새 줄을 만들지 않고 그 줄을 갱신한다. 키는 **이미지 파일명 + 출처 데이터셋 + 원래 split** 이다.
- 이미지를 열 때 그 사진의 사람 칸을 읽어 입력칸에 다시 보여 준다.

### 칸 구분

| 구분 | 칸 |
|---|---|
| 자동 | No · 이미지 파일명 · 라벨(TXT) 파일명 · 원본 BBox 수(처음 한 번만) · 최종 BBox 수 · Class · TXT 줄 수 = 화면 BBox 수 · 출처 데이터셋 · 원래 split |
| 사람 (`HUMAN_FIELDS`) | 이미지 유형 · 위치 맞음 · Class 맞음 · 누락 객체 여부 · 발견된 문제 · 작성자 · 검수자 · 검수일 · 비고(수정 내용) |
| 상태 | 사람이 이번에 직접 바꿨으면 그 값, 아니면 아래 규칙으로 자동 |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `HEADERS` | 19칸 머리글 (순서 고정) |
| `STATUS_*`, `STATUS_CHOICES` | 검수 전 · 수정 완료 · 검수 완료 · 수정 필요 · 제외 |
| `HUMAN_FIELDS`, `FORM_FIELDS` | 사람 칸 / `상태` + 사람 칸 (입력칸 화면이 다루는 칸) |
| `ManifestError` | 검수표를 읽거나 쓰지 못했을 때. **TXT 는 이미 저장된 뒤**라는 점에 주의 |
| `_load(path)` | `utf-8-sig` 로 읽음. 빈 파일 → 새 검수표. 머리글이 다르면 덮어쓰지 않고 중단. UTF-8 이 아니면 "CSV UTF-8 로 저장" 안내 |
| `_save(path, rows)` | 임시 파일 → `os.replace` (원자적). 엑셀이 파일을 잡고 있으면 안내 메시지 |
| `_find_row(rows, name, dataset, split)` | 키로 줄 찾기 |
| `_clean_human(human)` | 상태·사람 칸만 남김. `None` = 건드리지 않음, `""` = 지움. 정해진 값이 아닌 상태는 중단 |
| `read_human(image_path)` | 이 사진의 `FORM_FIELDS` 값 (없거나 RAW 밖이면 빈칸) |
| `read_status_map()` | 검수표 전체를 한 번 읽어 `{(데이터셋, split, 파일명): 상태}` — 썸네일 색·상태별 보기에 사용 |
| `status_of(image_path, status_map)` | 위 결과에서 이 사진의 상태 |
| `record_save(image_path, raw_txt, work_txt, screen_count, manifest_path=None, human=None, today=None)` | [저장] 직후 호출. 줄 생성·갱신 후 화면용 한 줄 메시지 반환 |

## 상태 자동 결정 (`record_save`)

"원본과 달라졌나"는 [`label_signature`](../yolo/yolo_loader.md) 비교로 판단한다. 원본 TXT 가 없으면 BBox 가 하나라도 있으면 "달라짐"으로 본다.

| 조건 | 결과 |
|---|---|
| 사람이 입력칸에서 상태를 **저장돼 있던 값과 다르게** 골랐다 | 그 값 |
| 달라졌고, 상태가 빈칸 / 검수 전 / 검수 완료 | **수정 완료** |
| 같고, 상태가 빈칸 / 수정 완료 (되돌린 경우) | **검수 전** |
| 수정 필요 · 제외 | 프로그램이 바꾸지 않음 |

- **검수일**: 상태가 검수 전이 아닌데 비어 있으면 오늘 날짜를 적는다. 이미 적힌 날짜(엑셀에서 고친 것 포함)는 바꾸지 않는다.
- **TXT 줄 수 = 화면 BBox 수**: 저장된 TXT 의 비어 있지 않은 줄 수와 저장 당시 화면 BBox 수가 같으면 `O`, 다르면 `X`.

## 의존성

- **사용하는 것**: [`settings`](../settings.md), [`data_paths.locate_in_raw`](../data_paths.md), [`yolo_loader`](../yolo/yolo_loader.md) (`label_signature`, `read_yolo_rows`)
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md), [`ui/form_panel`](../ui/form_panel.md) (`STATUS_CHOICES`), [`tools/merge_manifests`](../../tools/merge_manifests.md), 테스트 [`day1_selftest`](../../tests/day1_selftest.md) · [`test_manifest_input`](../../tests/test_manifest_input.md) · [`test_manifest_edge`](../../tests/test_manifest_edge.md) · [`test_merge_manifests`](../../tests/test_merge_manifests.md) · [`test_form_panel`](../../tests/test_form_panel.md) · [`test_filter_ui`](../../tests/test_filter_ui.md) · [`test_quick_review`](../../tests/test_quick_review.md) · [`test_thumb_strip`](../../tests/test_thumb_strip.md) · [`test_pack_results`](../../tests/test_pack_results.md)

## 사용 예

```python
from src.manifest.manifest_writer import record_save, read_human

msg = record_save(img, raw_txt, work_txt, screen_count=len(boxes),
                  human={"상태": "", "작성자": "김OO", "이미지 유형": "김치+대상"})
# '검수표 기록: No.12 · 상태 수정 완료 · BBox 3→4'
```

## 주의사항

- **RAW 밖의 이미지는 기록하지 않는다** (`"RAW 밖의 이미지라 검수표에는 기록하지 않았습니다."` 반환).
- 검수표 CSV 에는 실제 사진 파일명이 들어가서 회사 데이터로 본다. `.gitignore` 로 제외되어 있다.
- 엑셀에서 열어 둔 채 저장하면 Windows 에서 `ManifestError` 가 난다. 이때 TXT 는 이미 저장되었으므로 엑셀을 닫고 다시 저장하면 검수표만 갱신된다.
- 머리글을 엑셀에서 바꾸거나 열을 지우면 이후 저장이 모두 거부된다 (덮어써서 다른 칸을 잃지 않도록).
- 사람 칸 중 `None` 으로 넘긴 칸은 그대로 두고, 빈 글자 `""` 로 넘긴 칸은 지운다. 입력칸 화면은 이 구분을 지켜서 값을 넘긴다.
