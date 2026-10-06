# 3. Dataset Manifest 초안

> ⚠ **최종 기준은 팀의 검수표 틀 `manifests/dataset_manifest.xlsx` (시트 `검수표` 19칸, 상태: 검수 전 / 검수 완료 / 수정 필요 / 수정 완료 / 제외)** 입니다.
> 이 문서의 14칸·상태 7종은 1일차에 칸의 뜻을 이해하기 위한 **참고 초안**입니다. 차이는 [1일차 문서 모음](../../README.md) 참고.

> **Manifest(매니페스트) = 사진 한 장 한 장의 출처 · 상태 · 검수 이력을 적어 두는 작업대장(표)** 입니다.
> 1일차에는 **"어떤 칸을 만들고, 칸마다 무엇을 어떤 규칙으로 적을지"(초안)** 를 정합니다.
> 900줄을 채우는 일은 작업하면서 **프로그램이 자동으로** 합니다. (사람이 CSV 를 직접 만들 필요 없음)

---

## 1. Manifest 가 왜 필요한가

| 문제 상황 | Manifest 가 해결하는 방법 |
|---|---|
| 900장 중 어디까지 봤는지 기억이 안 난다 | `status` 로 장마다 상태가 남는다 |
| 누가 어느 사진을 작업했는지 모른다 | `assignee` / `reviewer` |
| 어떤 사진을 고쳤는지, 어떤 사진이 애매한지 모른다 | `status` = EDITED / REVIEW, `issue`, `note` |
| 같은 이름 사진이 데이터셋1·2 에 둘 다 있다 | `source_dataset` + `original_split` + `relative_path` 로 구분 |
| 교과 8 에서 train/validation 을 다시 나눠야 한다 | 원래 출처와 분할이 기록되어 있어야 가능 |
| 정상 김치 / 대상 단독 사진이 몇 장인지 알아야 한다 | `scene_type` |
| 원본 BBox 수와 최종 BBox 수가 얼마나 달라졌나 | `original_bbox_count` → `final_bbox_count` |

```text
교과 7  → 작업 배분 · 교차검수 · QA 통계에 사용
교과 8  → 출처 확인 · 기존 train/validation 확인 · 장면 유형 비율 확인 · 최종 분할 결정
```

> **한 줄 요약**: 사진 1장 = Manifest 1행. 900장이면 900행.

---

## 2. 전체 구조

```text
manifests/manifest.csv
┌──────────────────┬──────────┬───────┬────────┬────────────┬ …
│ image_name       │ source…  │ split │ status │ assignee   │
├──────────────────┼──────────┼───────┼────────┼────────────┤
│ 250424_….jpg     │ dataset1 │ train │ EDITED │ A          │   ← 사진 1장 = 1행
│ 250424_….jpg     │ dataset2 │ valid…│ PASS   │ B          │
└──────────────────┴──────────┴───────┴────────┴────────────┘
```

- **파일 위치**: `manifests/manifest.csv` (프로그램이 처음 저장할 때 자동 생성)
- **인코딩**: UTF-8 (BOM 포함) — 엑셀에서 한글이 안 깨짐
- **고유 키**: `relative_path` = `데이터셋/split/파일명`  → 같은 파일명이 다른 데이터셋에 있어도 구분됨
- **Git 에 올리지 않는다** (작업 기록과 데이터 출처 정보 — `.gitignore` 에 `manifests/` 등록됨)

---

## 3. 칸(필드) 상세 정의

### 3-1. 사진을 식별하는 칸 (프로그램이 자동으로 채움 — 사람이 고치지 않음)

| 필드 | 한글 뜻 | 형식 | 예 | 규칙 |
|---|---|---|---|---|
| `image_name` | 이미지 파일명 | 문자열 | `250424_000001.jpg` | 원본 파일명 그대로 |
| `label_name` | 라벨(TXT) 파일명 | 문자열 | `250424_000001.txt` | 이미지와 **기본 이름이 같음** |
| `source_dataset` | 출처 데이터셋 | 문자열 | `dataset1` | `images` 폴더 바로 위 폴더 이름 |
| `original_split` | 원래 분할 | `train` / `validation` | `validation` | 폴더 구조 그대로, **바꾸지 않음** |
| `relative_path` | 고유 주소(키) | `데이터셋/split/파일명` | `dataset2/validation/a.jpg` | **중복 불가** (표 전체에서 한 번만) |

### 3-2. 사진을 보고 사람이 판단·입력하는 칸

| 필드 | 한글 뜻 | 형식 / 허용값 | 필수? | 규칙 |
|---|---|---|:-:|---|
| `scene_type` | 이미지 유형 | `kimchi_with_target` `normal_kimchi` `object_only` `other_review` | 권장 | **Class 가 아니다.** YOLO TXT 에 들어가지 않는다 |
| `assignee` | 1차 작업자 | A, B … (이름·기호) | 필수 | 작업한 사람 |
| `reviewer` | 교차검수자 | A, B … | REVIEWED 일 때 필수 | **작업자와 달라야 함** |
| `issue` | 문제(REVIEW 이유) | 짧은 문장 | REVIEW 일 때 | 왜 애매한지 |
| `note` | 판단·수정 기록 | 자유 문장 | 권장 | 무엇을 왜 고쳤는지 |

### 3-3. 프로그램이 저장할 때 계산·기록하는 칸

| 필드 | 한글 뜻 | 형식 | 어떻게 정해지나 |
|---|---|---|---|
| `status` | 현재 상태 | §4 참고 | 사람이 고른 값 + 자동 규칙 (§5) |
| `original_bbox_count` | 원본(RAW) BBox 수 | 정수 | 사진을 **처음 열 때** 원본 TXT 의 정상 줄 수로 기록, 이후 **바뀌지 않음** |
| `final_bbox_count` | 현재/최종 BBox 수 | 정수 | **저장할 때마다** 화면의 BBox 수로 갱신 |
| `updated_at` | 마지막 저장 시각 | `2026-10-02T11:30:00` | 저장할 때마다 자동 |

> `original_bbox_count` 와 `final_bbox_count` 는 **빈 TXT 도 `0`** 으로 적습니다. (빈칸 ≠ 0)

---

## 4. 상태(status) 상세

```text
PENDING   아직 열어 보지 않음 (기본값)
        ↓ 사진을 열고 작업 시작
WORKING   작업 중 (상태를 고르지 않고 저장함)
        ↓
        ├─ PASS      기존 라벨이 정확해서 수정 없음
        ├─ EDITED    BBox/Class 를 고침 (추가·삭제·Class 변경·크기 수정)
        └─ REVIEW    판단이 어려워 다른 팀원 확인 필요
                ↓ 다른 팀원이 확인
        REVIEWED   교차검수 완료 (작업자 ≠ 검수자)
                ↓ 최종 QA 통과
        FINAL      교과 8 로 넘길 최종 확정
```

| 상태 | 언제 쓰나 | 이때 꼭 있어야 하는 것 |
|---|---|---|
| `PENDING` | 아직 안 본 사진 | — |
| `WORKING` | 보다가 중간에 저장 | — |
| `PASS` | 보니까 기존 라벨이 맞다 | `assignee`, BBox 수 변화 없음 |
| `EDITED` | 고쳤다 | `assignee`, `note`(무엇을 고쳤나) |
| `REVIEW` | 모르겠다 | `assignee`, **`issue`**(이유) |
| `REVIEWED` | 다른 사람이 확인했다 | **`reviewer`** (작업자와 다름) |
| `FINAL` | 최종 확정 | QA 완료, REVIEW 해결됨 |

### 이 상태일 때 이렇게 적는다 (상황별)

| 상황 | status | 적을 것 |
|---|---|---|
| 기존 라벨이 맞다 | PASS | `note`: "이상 없음" (선택) |
| 빠진 이물 BBox 를 추가했다 | EDITED | `note`: "나뭇가지 1개 추가", 2 → 3 |
| 불필요한 BBox 를 삭제했다 | EDITED | `note`: "잘못된 BBox 1개 삭제", 3 → 2 |
| Class 만 바꿨다 | EDITED | `note`: "3 → 2 로 변경" (BBox 수는 그대로) |
| 정상 김치(빈 TXT)가 맞다 | PASS | `scene_type`: normal_kimchi, 0 → 0 |
| Class 4 로 보이는 BBox 가 있다 | REVIEW | `issue`: "Class 4 의심", 지우지 않음 |
| 위치/종류가 애매하다 | REVIEW | `issue`: 이유 |
| 다른 사람이 검수를 끝냈다 | REVIEWED | `reviewer` 입력 |

---

## 5. 프로그램이 Manifest 를 채우는 방법 (실제 동작)

라벨링 프로그램(v1·v2)의 화면 입력이 어느 칸으로 들어가는지:

| 화면 | → Manifest 칸 |
|---|---|
| 사진을 열 때(자동) | `image_name` `label_name` `source_dataset` `original_split` `relative_path`, 처음이면 `original_bbox_count` |
| 오른쪽 **검수 상태** (PASS / EDITED / REVIEW / REVIEWED) | `status` |
| **작업자** 칸 | `assignee` |
| **검수자** 칸 | `reviewer` |
| **Scene Type** 선택 | `scene_type` |
| **Issue / Note** 칸 | `note` (상태가 REVIEW 이면 같은 내용이 `issue` 에도 들어감) |
| [저장] 할 때(자동) | `final_bbox_count`, `updated_at`, `status` 확정 |

### 자동 규칙

| 규칙 | 설명 |
|---|---|
| BBox 를 고치면 자동 EDITED | 상태가 비어 있거나 PASS 인데 BBox 가 원본과 달라지면 **EDITED 로 바뀜** |
| 상태를 안 고르고 **[저장+다음]** | 원본과 같으면 **PASS**, 달라졌으면 **EDITED** |
| 상태를 안 고르고 **[저장]** | 원본과 같으면 **WORKING**, 달라졌으면 **EDITED** |
| **REVIEWED** 저장 조건 | 검수자가 있고 **작업자와 달라야** 저장됨 (아니면 경고 후 저장 안 됨) |
| 파일이 안 깨지게 저장 | 임시 파일에 쓴 뒤 교체 (저장 도중 실패해도 기존 Manifest 보존) |

### 알아 둘 점

- **열어만 보고 저장하지 않은** 사진은 `PENDING` 으로 남습니다. (저장해야 상태가 바뀜)
- `original_bbox_count` 는 TXT 의 **읽을 수 있는 줄**만 셉니다. 형식이 깨진 줄은 세지 않습니다. → 깨진 줄은 `issue`/이슈 기록에 따로 적습니다.
- 현재 1일차 프로그램은 **Manifest 를 만들지 않습니다.** 상태 기록 기능은 개발 예정이며, 최종 형식은 `manifests/dataset_manifest.csv` 입니다.

---

## 6. 일관성 규칙 (값이 이상하지 않은지 검사하는 기준)

| 번호 | 규칙 | 어기면 |
|---|---|---|
| R1 | `relative_path` 는 표 전체에서 **중복이 없다** | 같은 사진이 두 번 기록됨 → 하나 삭제 아닌 **원인 확인** |
| R2 | `status` 는 §4 의 7개 값 중 하나 | 오타 → 수정 |
| R3 | `PASS` 이면 `original_bbox_count == final_bbox_count` | 고쳤으면 EDITED |
| R4 | `REVIEW` 이면 `issue` 가 비어 있지 않다 | 이유를 적는다 |
| R5 | `REVIEWED` 이면 `reviewer` 가 있고 `assignee` 와 다르다 | 다른 사람이 검수 |
| R6 | `scene_type` 은 허용 4개 값 또는 빈칸 | 새 값을 만들지 않는다 |
| R7 | `original_split` 은 `train` 또는 `validation` | 임의 변경 금지 |
| R8 | 빈 TXT 사진은 `0` 으로 적혀 있다 (빈칸 아님) | 0 으로 |
| R9 | `FINAL` 인데 `issue` 가 남아 있는 REVIEW 이력은 해결 기록이 `note` 에 있다 | 근거 기록 |

---

## 7. 작성 예시 (가짜 샘플 12장 중 일부, 상황별)

| image_name | source_dataset | original_split | scene_type | assignee | reviewer | status | bbox 수 | issue | note |
|---|---|---|---|---|---|---|---|---|---|
| 250424_000001.jpg | 샘플데이터1 | train | kimchi_with_target | A | | EDITED | 2 → 3 | | 병해·갈변 1개 추가 |
| 250424_000002.jpg | 샘플데이터1 | train | normal_kimchi | A | | PASS | 0 → 0 | | 이물 없음 확인 (빈 TXT 정상) |
| 250424_000003.jpg | 샘플데이터1 | train | kimchi_with_target | B | | EDITED | 1 → 1 | | Class 1 → 2 로 변경 |
| 250424_000005.jpg | 샘플데이터1 | train | object_only | A | | PASS | 1 → 1 | | 대상 단독, 정상 |
| 250424_000102.jpg | 샘플데이터2 | train | kimchi_with_target | B | | REVIEW | 1 → 1 | Class 4 의심 | 고무장갑으로 보이나 확신 없음 |
| 250424_000104.jpg | 샘플데이터2 | train | kimchi_with_target | A | C | REVIEWED | 2 → 2 | | C 가 교차검수 완료, 수정 없음 |
| 250424_000201.jpg | 샘플데이터2 | validation | kimchi_with_target | C | | EDITED | 2 → 1 | | 불필요한 BBox 1개 삭제 |

> 위 이미지·값은 모두 **가짜 샘플 기준 예시**입니다. 실제 값은 작업하면서 채워집니다.

### 잘못 쓴 예 → 올바른 예

| 잘못 | 이유 | 올바르게 |
|---|---|---|
| `status` 가 `통과` | 허용 값이 아님 | `PASS` |
| `scene_type` 이 `정상김치` | 허용 값이 아님 | `normal_kimchi` |
| PASS 인데 `2 → 3` | 고쳤으면 PASS 가 아님 | `EDITED` |
| REVIEW 인데 `issue` 가 비어 있음 | 이유를 모름 | "Class 4 의심" 처럼 적기 |
| REVIEWED 인데 `assignee = reviewer = A` | 자기가 자기 검수 | 다른 사람이 검수 |
| 빈 TXT 사진의 bbox 수가 빈칸 | 0 과 빈칸은 다르다 | `0 → 0` |
| `original_split` 을 `val` 로 적음 | 원래 이름을 바꿈 | `validation` |

---

## 8. 파일 운영 규칙

| 항목 | 규칙 |
|---|---|
| 직접 편집 | 가능하면 **프로그램에서만** 수정. 엑셀로 열 때는 **읽기 위주** |
| 엑셀로 저장해야 한다면 | **CSV UTF-8** 로 저장 (일반 CSV 는 한글이 깨짐), 머리글(첫 줄)을 지우지 않음 |
| 열 순서·이름 | **바꾸지 않는다** (프로그램이 이 이름으로 읽음) |
| 백업 | 작업 후 `manifest.csv` 를 날짜를 붙여 복사해 둔다 (예: `manifest_20261002.csv`) |
| 여러 명이 작업할 때 | 각자 PC 에 따로 생기므로 **담당 범위를 나눠** 작업하고, 제출 후 담당자가 하나로 합친다 (같은 사진을 두 명이 작업하지 않음) |
| 취합 시 충돌 | 같은 `relative_path` 가 두 번 나오면 **둘 다 보존해서 원인 확인**, 마음대로 하나를 지우지 않는다 |
| 보안 | Manifest 에는 파일명·출처가 들어 있으므로 데이터와 같은 수준으로 외부 공유를 피한다 |

---

## 9. Manifest 로 알 수 있는 것 (집계 예)

| 알고 싶은 것 | 보는 방법 |
|---|---|
| 얼마나 진행됐나 | `status` 별 개수 (PENDING 이 줄어들수록 진행) |
| 수정이 많았던 사진 | `status = EDITED` 개수, `original → final` 차이 |
| 남은 애매한 사진 | `status = REVIEW` 목록과 `issue` |
| 출처별 비율 | `source_dataset`, `original_split` 별 개수 |
| 장면 유형 비율 | `scene_type` 별 개수 (교과 8 분할 참고) |
| 작업자별 처리량 | `assignee` 별 개수 |
| 교차검수 진행 | `reviewer` 가 채워진 개수 |

한계: Manifest 의 BBox 수 변화로는 **"몇 개가 늘었는지/줄었는지" 정도만** 알 수 있습니다. 추가·삭제·Class 수정을 각각 몇 건 했는지 정확히 세려면 원본과 최종 TXT 를 비교하는 별도 QA(3일차 이후)가 필요합니다.

---

## 10. 파일 형식 (참고)

프로그램이 만드는 CSV 의 첫 줄(열 순서 고정):

```csv
image_name,label_name,source_dataset,original_split,relative_path,scene_type,assignee,reviewer,status,original_bbox_count,final_bbox_count,issue,note,updated_at
```

> 1일차 산출물로는 **이 문서의 칸 정의와 규칙**이면 충분합니다. CSV 파일은 라벨링 프로그램이 자동으로 만듭니다.

---

## 11. 팀이 정할 것 (【합의】)

| 질문 | 합의 내용 |
|---|---|
| 작업자 이름은 이름 / 기호(A, B) 중 무엇으로 적나? | 【합의】 |
| `scene_type` 은 누가 판단하나? (작업자 / 검수자) | 【합의】 |
| PASS 사진도 `note` 를 적나? (예: "이상 없음") | 【합의】 |
| REVIEW 가 해결되면 `issue` 를 지우나, 남기고 `note` 에 결과를 적나? | 【합의】 (권장: `issue` 는 남기고 `note` 에 결론) |
| Manifest 백업 주기와 담당 | 【합의】 |
| 여러 명 결과를 합치는 방법 (누가, 언제, 어떻게) | 【합의】 |

## 12. 1일차 점검

- [ ] Manifest 가 무엇이고 왜 필요한지 설명할 수 있다
- [ ] 칸 14개의 뜻을 알고, 어느 칸이 자동이고 어느 칸이 사람이 쓰는 칸인지 구분할 수 있다
- [ ] 상태 7개의 순서와 PASS / EDITED / REVIEW 의 차이를 설명할 수 있다
- [ ] `scene_type` 이 YOLO Class 가 아니라는 것을 설명할 수 있다
- [ ] 일관성 규칙(R1~R9)을 알고 있다
- [ ] 팀 합의 항목(§11)을 정했거나 2일차로 넘기기로 했다
