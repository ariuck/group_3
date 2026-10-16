# `tools/qa_summary.py`

> 검수표와 라벨(RAW·WORK)을 읽어 **QA Summary**(`reports/qa_summary.md`)를 만든다. 검수 현황, BBox 변화, Class 별 증감, 이미지 유형, Validation, 완료 기준 점검을 담는다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tools/qa_summary.py)

## 사용법

```bash
python tools/qa_summary.py            # 화면에 미리보기
python tools/qa_summary.py --apply    # reports/qa_summary.md 로 저장
```

사진 크기를 읽어야 해서 900장 기준 몇 분이 걸릴 수 있다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `REPORT_PATH` | `reports/qa_summary.md` |
| `REVIEW_DECISIONS`, `REVIEW_CONFIRMERS` | REVIEW 이력 사진의 최종 판단과 확인자 (사람이 정한 기록, [records/이슈기록](../project/records/이슈기록.md) 과 같은 내용) |
| `HUMAN_FINAL_QA` | Human Final QA 수행 기록 (날짜·점검자·장수·결과) |
| `read_manifest(path)` | 검수표 CSV → dict 목록 |
| `_boxes(label_path, w, h)` | 라벨 → [`bbox_diff`](../src/bbox/bbox_diff.md) 용 픽셀 BBox |
| `collect(raw_dir, work_dir, manifest_path)` | 사진마다 RAW ↔ 최종(WORK 우선) 을 비교해 추가·수정·삭제·그대로, Class 이동, 데이터셋별 바뀐 사진 수, "라벨 변화와 상태(수정 완료)의 불일치" 수를 셈 |
| `build_markdown(stats, validation, today)` | 8개 장: 결론 · 검수 현황 · BBox 변화 · 이미지 유형 · Validation · Human QA · 완료 기준 점검 · 검수 기간과 REVIEW 기준 |
| `main(argv)` | `collect()` + [`validate_dataset()`](../src/validation/validator.md) → Markdown |

### 최종 판정 (`verdict`)

`사진 수 > 0` 이고 아래가 모두 0 이면 **"교과 8 사용 가능"**:
- 상태가 검수 완료·수정 완료가 아니거나 검수자가 빈 사진 + CRITICAL 이 있는 사진
- 미처리 REVIEW (`수정 필요` + `발견된 문제` 가 `REVIEW` 로 시작)
- 작성자 = 검수자인 줄

## 의존성

- **사용하는 것**: [`src/settings`](../src/settings.md), [`src/bbox/bbox_diff`](../src/bbox/bbox_diff.md), [`src/validation/validator`](../src/validation/validator.md), Pillow
- **사용하는 곳**: 직접 실행 (README §12), [`tests/test_qa_summary`](../tests/test_qa_summary.md)

## 주의사항

- **데이터와 상관없이 고정된 문장이 있다.** 사람 이름(실측·판정 확인자, REVIEW 확인자, Human QA 점검자), Human QA 결과, "TINY_BOX 경고 1건을 확인 후 삭제", "이미지·TXT Pair 900 / 900" 은 코드에 직접 적혀 있다. 다른 데이터로 다시 만들면 이 부분은 실제와 다를 수 있으니 직접 고쳐야 한다.
- RAW 에 사진이 없는 검수표 줄은 통계에서 조용히 빠진다.
- 보고서에 실제 사진 파일명은 넣지 않는다.
