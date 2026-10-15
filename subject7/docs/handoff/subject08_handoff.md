# 교과 8 Handoff

> 교과 7(조각김치 이물검출 라벨링)의 결과를 교과 8(Object Detection 학습)에서 바로 쓸 수 있도록 **무엇이 어디에 있고, 무엇을 지켜야 하는지** 한곳에 정리한 문서입니다.
> 숫자는 2026-10-08 기준 검수표와 라벨에서 읽은 값이며, 자세한 통계는 [QA Summary](../../reports/qa_summary.md) 에 있습니다.
>
> **데이터 성격**: 본 프로젝트는 AI캠퍼스 교육을 위해 실제 산업데이터와 유사한 분포 구조로 100% 가상 생성된 조각김치 이물검출 학습데이터를 활용하여 수행하였습니다. 실제 생산라인 원본 데이터라고 표현하지 않습니다.

## 1. FINAL Dataset 수량

| 항목 | 수량 |
|---|---:|
| FINAL 이미지 | 900장 |
| FINAL YOLO TXT | 900개 (빈 TXT 0개) |
| 이미지 ↔ TXT Pair | 900 / 900 |
| BBox | 4561개 (원본 4399개에서 추가 166 · 수정 173 · 삭제 4) |

출처별 수량 (`검수표.csv` 의 `출처 데이터셋` · `원래 split` 으로 구분):

| 출처 데이터셋 | 원래 split | 사진 |
|---|---|---:|
| 이물검출_학습데이터1 | train | 500 |
| 이물검출_학습데이터2 | train | 220 |
| 이물검출_학습데이터2 | validation | 180 |

## 2. FINAL Dataset 저장 위치

```text
data/final/
├── images/
│   ├── train/            학습용 이미지 720장 (.jpg)
│   └── validation/       검증용 이미지 180장 (.jpg)
├── labels/
│   ├── train/            학습용 YOLO TXT 720개 (이미지와 같은 이름)
│   └── validation/       검증용 YOLO TXT 180개
├── classes.txt           Class 0~6 이름 (번호 순서, 한 줄에 하나)
├── 검수표.csv             900장의 검수 기록 (출처·원래 split 포함)
└── dataset_manifest.xlsx 같은 내용의 엑셀 (제출용)
```

- 사진은 RAW 의 복사본, 라벨은 검수한 `data/work` 라벨입니다. 수량·짝·Class 분포의 근거: [final_evidence](../../reports/final_evidence.md)
- **원래의 train / validation 구분을 폴더로 유지했습니다.** 학습데이터1 train 500 + 학습데이터2 train 220 = `train` 720장, 학습데이터2 validation = `validation` 180장입니다. 새로 나누거나 섞지 않았습니다. (재구성은 교과 8 에서 결정)
- 어느 데이터셋(학습데이터1·2)에서 왔는지는 `검수표.csv` 의 `출처 데이터셋` 칸에서 확인합니다.
- 다른 구조가 필요하면 `python tools/build_final.py --apply --overwrite --layout flat`(한 폴더) 또는 `--layout nested`(`<데이터셋>/images|labels/<split>/`) 로 다시 만들 수 있습니다.

## 3. YOLO Label 형식

```text
class_id x_center y_center width height
```

- 한 줄에 BBox 하나, 좌표는 0~1 비율값(이미지 크기로 나눈 값)입니다. 예: `2 0.7565104167 0.1622685185 0.0473958333 0.0615740741`
- 이미지 1장 = TXT 1개이며 이름이 같습니다. 정상 김치·이물 없음에 해당하는 빈 TXT 는 없습니다.

## 4. Class 정보

| Class | 이름 | 최종 BBox 수 |
|---:|---|---:|
| 0 | 나뭇잎·종이류 | 727 |
| 1 | 플라스틱류·돌·금속류 | 1852 |
| 2 | 나뭇가지류 | 932 |
| 3 | 벌레류 | 379 |
| 4 | 고무장갑 (사용 안 함) | 0 |
| 5 | 병해·갈변 | 416 |
| 6 | 파·고추 | 255 |

- 회사 제공 번호 그대로입니다. 번호를 바꾸거나 새 Class 를 만들지 않았습니다. 설정 파일은 `configs/classes.yaml`, 같은 이름 목록은 `data/final/classes.txt` 입니다.
- Class 5(병해·갈변)는 원본 313 → 416 으로 가장 많이 보강되었습니다. Class 별 성능을 볼 때 참고하세요.

## 5. 최종 QA 결과

| 항목 | 결과 |
|---|---|
| Validation (전체 900장) | CRITICAL 0 · WARNING 0 · INFO 0 |
| 최종 FAIL | 0건 |
| 최종 REVIEW (미처리) | 0건 |
| 검수 상태 | 검수 완료 674 · 수정 완료 226 (검수 전·수정 필요·제외 0) |
| 작성자와 검수자가 같은 사진 | 0장 |
| 교차검수 범위 | 900장 전부 (작성자와 다른 사람이 검수). 라벨이 원본과 달라진 235장도 모두 포함 |
| PASS(검수 완료) 사진의 표본검수 | 전수 교차검수라 100% (가이드 권장 20~30% 이상) |
| 최종 잔여 이슈 | 없음 (미처리 REVIEW 0 · Validation 0 · 검수 전·수정 필요·제외 0) |
| 프로그램 Acceptance Test (가이드 §7.5) | 2026-10-08, 테스터 손상우 — 16단계 모두 통과 ([Test Report](../../reports/test_report.md) §4) |
| Human Final QA (가이드 §7.3 우선순위 점검) | 2026-10-08, 강동연 — 40장 점검(Class 변경 1 · 작은 BBox 30 · BBox 많은 이미지 9), 이상 없음, 수정 0건 ([점검 목록](../../reports/human_qa_worklist.md)) |
| REVIEW 이력 2장 (180번 · 601번) | 지혜성 · 김석범 확인. 180번은 잎사귀로 보기에는 너무 작아 갈변(Class 5)으로 라벨링, 601번은 REVIEW 로 잘못 표시된 것을 바로잡음 ([이슈 기록](../records/이슈기록.md)) |
| 최종 QA 판정 | **교과 8 사용 가능** |

자세한 내용: [QA Summary](../../reports/qa_summary.md) · 프로그램 시험: [Test Report](../../reports/test_report.md)

## 6. Dataset Manifest 위치와 칸 대응

- 위치: `manifests/dataset_manifest.csv` (제출 파일) · `data/final/검수표.csv` · `data/final/dataset_manifest.xlsx`
- 칸 설명: [manifest_guide](../standards/manifest_guide.md)

교과 8 에서 특히 쓰는 값과 우리 검수표의 칸 대응:

| 교과 8 에서 필요한 값 | 우리 검수표의 칸 |
|---|---|
| `file_name` | `이미지 파일명` (`라벨(TXT) 파일명`) |
| `source_dataset` | `출처 데이터셋` |
| `original_split` | `원래 split` |
| `status` (DONE / EDITED / REVIEW) | `상태` — 검수 완료 = DONE · 수정 완료 = EDITED · 수정 필요(`발견된 문제`가 `REVIEW:` 로 시작) = REVIEW |
| `qa_status` (PASS / WAIT) | `검수자` 칸이 채워지고 `상태`가 검수 완료·수정 완료이면 PASS, 아니면 WAIT. 지금은 900장 모두 PASS |
| `worker` | `작성자` (검수자는 `검수자`) |
| `review_reason` | `발견된 문제` (`REVIEW: 이유 코드`) |
| `scene_type` | `이미지 유형` — 김치+대상 객체 = `kimchi_with_target` · 정상 김치 = `normal_kimchi` · 대상 객체 단독 = `object_only` · 판단 어려움 = `other_review` |

## 7. Class / BBox 기준서 위치

| 문서 | 위치 |
|---|---|
| Class 기준서 | [docs/standards/class_guide.md](../standards/class_guide.md) |
| BBox 기준서 | [docs/standards/bbox_guide.md](../standards/bbox_guide.md) |
| Project Baseline | [docs/standards/project_baseline.md](../standards/project_baseline.md) |
| 검수 분담 | [docs/team/검수_배정.md](../team/검수_배정.md) |

## 8. 교과 8 에서 알아 둘 점

- **정상 김치(이물 없는) 사진이 0장**입니다. 이미지 유형은 김치+대상 객체 749 · 대상 객체 단독 150 · 판단 어려움 1 입니다. 모든 사진에 BBox 가 한 개 이상 있어서, 이물이 없는 사진에서 "없다"고 맞히는 능력은 이 데이터로는 학습·평가하기 어렵습니다.
- 비슷한 사진이 Train 과 Test 에 함께 들어가는 Data Leakage 를 확인할 때 `검수표.csv` 의 출처·원래 split·이미지 유형을 사용하세요.
- 기존 validation(180장)은 학습데이터2 한 곳에서만 왔습니다.
- **중복·유사 장면 주의**: 파일명 앞 6자리(날짜로 보임: 250410 · 250411 · 250424 · 250513)가 train 과 validation 에 모두 나타납니다. 같은 때 찍힌 비슷한 장면이 양쪽에 나뉘어 있을 수 있으니, 학습 전에 Data Leakage(유사 사진 중복)를 점검하세요.
- **FINAL Freeze**: `data/final` 은 2026-10-08 에 `tools/build_final.py` 로 만들었고 직접 고치지 않습니다. 라벨 문제를 찾으면 `data/work` 를 고치고 Validation · 검수 후 `python tools/build_final.py --apply --overwrite` 로 다시 만드세요.
- 라벨을 더 고치면 최종본을 다시 만들어야 합니다: `python tools/build_final.py --apply --overwrite` (옛것은 `data/backup` 으로 옮김).

## 9. 교과 8 로 넘어가기 전 최소 확인

| 확인 항목 | 결과 |
|---|:-:|
| FINAL 이미지가 준비되어 있다 | ✅ 900장 |
| FINAL YOLO TXT 가 준비되어 있다 | ✅ 900개 |
| 이미지와 TXT Pair 가 정상이다 | ✅ 900 / 900 |
| Class ID / Class Name 이 확정되어 있다 | ✅ 0~6 (Class 4 미사용) |
| 기존 데이터 출처와 Split 정보를 확인할 수 있다 | ✅ `검수표.csv` |
| 미처리 REVIEW 가 없다 | ✅ 0건 |
| Validation Critical Error 가 없다 | ✅ 0건 |
| QA 결과가 최종 완료 상태이다 | ✅ [QA Summary](../../reports/qa_summary.md) |

다음 단계는 교과 8 에서 합니다: `Train / Validation / Test 구성 → dataset.yaml 작성 → YOLO Object Detection 학습`

## 10. 지켜야 할 것

- **데이터(사진·TXT·검수표·최종본)는 회사 데이터(NDA)입니다.** Git, 개인 클라우드, 메신저로 보내지 않습니다. (`data/` 와 검수표 CSV 는 `.gitignore` 에 있습니다)
- RAW 원본은 수정하지 않습니다.
- 학습 전에 `python tools/build_final.py` 로 조건(검수 상태·검수자·짝·Validation)을 다시 확인할 수 있습니다.

## 11. 교과 8 에서 정할 것

- train / validation / test 구성 방식 (원래 split 은 `검수표.csv` 에 있음)
