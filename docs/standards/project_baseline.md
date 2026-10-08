# Project Baseline

> 우리 팀이 교과 7 프로젝트(조각김치 이물검출 라벨링)를 **어떤 기준으로 진행했고 어떤 결과를 냈는지** 한곳에 정리한 공통 기준 문서입니다.
> 수치는 2026-10-08 기준 검수표(`manifests/dataset_manifest.csv`), 라벨, Git 기록(`main`)에서 읽은 값입니다.
> `【기입】` 은 팀이 직접 확인해서 적는 칸이고, `【확인 필요】` 는 근거를 더 확인해야 하는 칸입니다. (임의로 채우지 않습니다)

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 프로젝트 | 교과 7 — 조각김치 이물검출 라벨링 |
| 목표 | 회사 제공 이미지 900장의 YOLO Detection 라벨을 검수·수정해, 교과 8(Object Detection 학습)에서 바로 쓸 수 있는 FINAL 데이터를 만든다 |
| 만든 것 | ① 라벨링 프로그램(Python · Tkinter · Pillow) ② 검수 보조 도구(합치기·묶기·공유 서버·최종본·QA 보고서) ③ 기준서(Class · BBox · 검수표) ④ FINAL 데이터 900장 ⑤ QA·시험 보고서와 교과 8 Handoff |
| 기간 | 2026-10-06 ~ 2026-10-08 (Git 기록 기준) |
| 결과 | 900장 모두 검수 완료. 미처리 REVIEW 0 · Validation 오류 0 · 최종 FAIL 0 ([QA Summary](../../reports/qa_summary.md)) |

### 교과 7 산출물 11개와 우선순위

11개 모두 제출 대상이고, 일정이 빠듯할 때 **P1 → P2 → P3 순서로 완성**합니다. (배점은 권장 배점)

| 순위 | 산출물 | 우선순위 | 배점 | 위치 |
|---:|---|:-:|---:|---|
| 1 | FINAL YOLO 라벨 데이터 및 증빙 | P1 | 25 | `data/final/` · [reports/final_evidence.md](../../reports/final_evidence.md) |
| 2 | Class 기준서 | P1 | 10 | [class_guide.md](class_guide.md) |
| 3 | Dataset Manifest | P1 | 12 | `manifests/dataset_manifest.csv` · [manifest_guide.md](manifest_guide.md) |
| 4 | QA Summary | P1 | 13 | [reports/qa_summary.md](../../reports/qa_summary.md) |
| 5 | 라벨링 프로그램 | P2 | 12 | `main.py` · `src/` |
| 6 | BBox 기준서 | P2 | 7 | [bbox_guide.md](bbox_guide.md) |
| 7 | 교과 8 Handoff | P2 | 6 | [subject08_handoff.md](../handoff/subject08_handoff.md) |
| 8 | 소스코드 | P3 | 7 | `src/` · `tools/` · `tests/` · `requirements.txt` · `configs/classes.yaml` |
| 9 | Test Report | P3 | 4 | [reports/test_report.md](../../reports/test_report.md) |
| 10 | README | P3 | 2 | [README.md](../../README.md) |
| 11 | Project Baseline | P3 | 2 | 이 문서 |

---

## 2. 팀 구성과 역할

팀원은 **6명**입니다: 강동연 · 김동훈 · 김석범 · 손상우 · 이후영 · 지혜성

### 역할 분담

| 역할 | 책임 | 담당 |
|---|---|---|
| ① PM / 문서 | 기준선·일정, Git 병합(`main`), 문서·README, 교과 8 인계, 검수 도구와 결과 취합 | 강동연 |
| ② GUI / 이미지 | 화면, 이미지 표시, 이전/다음 이동, 진행률 | 이후영 |
| ③ BBox / 좌표 | BBox 추가·수정·삭제, 화면↔원본 좌표, Zoom/Pan, Undo | 김석범 |
| ④ 라벨 저장 / 데이터 | Class, TXT Load/Save, 검수표(Manifest), RAW/WORK 관리, 검수 기록 입력칸 | 김동훈 |
| ⑤ QA / 검증 | Validation, Golden/Pilot 시험, 이슈 기록 | 지혜성 |
| 라벨 작성 · 검수 참여 | 라벨 작성(작성자 칸에 기록), 교차검수 | 손상우 【기입】 (역할 표기는 팀이 확인) |

### 실제 기여 (Git 기록과 검수표 기준)

| 팀원 | GitHub 계정 | main 의 커밋 | 주요 내용 | 라벨 작성 | 교차검수 |
|---|---|---:|---|---:|---:|
| 강동연 | `ariuck` | 169 (병합 46 포함) | 프로젝트 기본 구조, Class 설정, YOLO TXT Load/Save, RAW 보호, BBox 편집·Diff, 검수 화면(빠른 검수·단축키·필터), 검수표 자동 기록, 렉 개선, 검수 도구(가져오기·합치기·묶기·최종본·QA 보고서), 근거리 공유 서버, 문서 전체, `main` 병합 | 52장 | — |
| 지혜성 | `Hyesung` (`wlgptjd333`) | 8 | 900장 무결성 검증(`validate_dataset`)과 결과 창, 검증 시험 11종, Golden/Pilot 시험 보고서, 작성자 이름 통일(`.mailmap`) | 140장 | 350장 |
| 김동훈 | `ccbb1296` | 3 | 검수 기록 입력칸(상태·작성자·검수자·이미지 유형·발견된 문제·비고), 사진 목록 패널과 이동 개선, WSL 한글 입력(두벌식 조합기) | 180장 | 350장 |
| 이후영 | `Hu250506` | 1 | 폴더 열기·이전/다음 이동(navigator)과 `main_window` 연결 | 120장 | 200장 |
| 김석범 | `tjrqja021206` | 3 | Zoom·Pan 좌표 변환(viewport), BBox Undo/Redo(history)와 화면 연결 | 220장 | — |
| 손상우 | — | 0 | (Git 커밋 없음) | 188장 | — |

- 위 GitHub 계정과 이름의 짝은 **브랜치 이름(`feature/donghun` 등)과 담당 기능으로 맞춘 것**이라 팀 확인이 필요합니다. 【확인 필요】
- 커밋이 있는 팀원 5명(손상우 제외)의 작업이 모두 `main` 에 들어 있습니다. 팀원 브랜치 4개와 `feat/hyesung` 은 모두 `main` 에 병합되었습니다. (`main` 에 아직 없는 커밋 0개)
- 라벨 작성자는 검수표 `작성자` 칸 기준입니다. 6명이 작성한 사진 합계는 900장입니다. (손상우 188 · 김석범 220 · 김동훈 180 · 지혜성 140 · 이후영 120 · 강동연 52)
- **`main` 병합은 PM 강동연이 맡았습니다.** 병합 커밋 49개 중 46개가 강동연 계정이고, 나머지 3개는 지혜성 계정이 만든 병합 커밋(GitHub Pull Request #1 · #2 병합 포함)입니다.

> Figma 보드(3조)에는 조직도와 1~2일차 작업내역, 4일차 검수 분담, Class/BBox 기준표 프레임이 있습니다. 화면이 작아 프레임 제목만 확인했습니다. 보드에 적힌 역할 표기와 분담 숫자가 위 표와 다르면 보드를 기준으로 고칩니다. 【확인 필요】

---

## 3. 공통 데이터 기준

- 전체 이미지: 900장 (JPG) + YOLO TXT 900개, 짝 900 / 900
  - 이물검출_학습데이터1 / train: 500 · 이물검출_학습데이터2 / train: 220 · 이물검출_학습데이터2 / validation: 180
- 번호는 프로그램 화면의 `N / 900` 과 같다. (데이터셋 → split → 파일명 순: 1~500 · 501~720 · 721~900)
- Label Format: YOLO Detection TXT (`class_id x_center y_center width height`, 0~1 비율값)
- Class: 0~6 (회사 제공 번호 그대로, 재번호 금지) — 설정 파일 `configs/classes.yaml`
- Class 4(고무장갑): 사용하지 않음 (발견 시 삭제하지 않고 REVIEW). 실제로 한 개도 없다
- 기존 `train / validation` 구분과 데이터셋 출처는 **기록으로 유지**한다 (검수표의 `출처 데이터셋`·`원래 split` 칸). 검수는 합치지 않고 데이터셋별로 했고, `train / validation` 을 다시 나누는 것은 교과 8 에서 한다
- RAW 데이터 수정 금지

| Class | 이름 | 원본 BBox | 최종 BBox |
|---:|---|---:|---:|
| 0 | 나뭇잎·종이류 | 716 | 727 |
| 1 | 플라스틱류·돌·금속류 | 1831 | 1852 |
| 2 | 나뭇가지류 | 911 | 932 |
| 3 | 벌레류 | 379 | 379 |
| 4 | 고무장갑 (사용 안 함) | 0 | 0 |
| 5 | 병해·갈변 | 313 | 416 |
| 6 | 파·고추 | 249 | 255 |
| | **합계** | **4399** | **4561** |

### 데이터 폴더

| 폴더 | 용도 | Git |
|---|---|:-:|
| `data/raw/` | 회사 제공 원본. 읽기만 한다 (프로그램이 저장을 거부) | 제외 |
| `data/work/` | 작업본. RAW 와 같은 구조로 수정한 라벨(TXT)만 저장 | 제외 |
| `data/final/` | 최종본. `images/` · `labels/` · `classes.txt` · `검수표.csv` · `dataset_manifest.xlsx` | 제외 |
| `data/backup/`, `data/share/` | 합치기·교체 전 백업, 결과 zip | 제외 |
| `manifests/dataset_manifest.csv` | 작업 상태 기록(검수표). 실제 사진 파일명이 있어 회사 데이터로 본다 | 제외 |

---

## 4. 작업 진행 (단계별)

Git 기록은 2026-10-06 ~ 10-08 에 걸쳐 있고, 날짜별 커밋 수는 10-06: 91 · 10-07: 35 · 10-08: 9 (병합 제외)입니다. 회의록은 내용 기준으로 일차를 나눕니다.

| 단계 | 한 일 | 기록 |
|---|---|---|
| 1일차 | RAW/WORK/FINAL 분리, 이미지 1장 열기 → TXT Load → BBox 편집 → WORK 저장 → 다시 불러오기 (End-to-End), 데이터 조사, Class/BBox 기준 정리, 검수표 설계 | [회의록](../meetings/회의록_1일차.md) · [Gate 체크리스트](../team/Gate_체크리스트.md) |
| 2일차 | 이전/다음 이동, Zoom/Pan, 저장 안 한 변경 보호, 상태·작성자·검수자 입력칸, Validation, Golden Test | [회의록](../meetings/회의록_2일차.md) · [역할분담](../team/역할분담_DailyGate.md) |
| 3일차 | BBox 이동·크기 조절, RAW 와 Diff 보기, 상태별 필터, 한 키 검수(`Enter`·`R`·`N`), 렉 개선, 검수표 점검, 한글 입력 | [회의록](../meetings/회의록_3일차.md) |
| 4일차 | 6대 PC의 라벨·검수표를 모아 900장 교차검수, 근거리 공유 서버, 합치기·묶기 도구, 최종본·QA 보고서 | [검수 배정](../team/검수_배정.md) · [결과 주고받기](../team/결과_주고받기.md) |
| 마무리 | FINAL 데이터 생성, QA Summary, 증빙, Handoff, 시험 보고서 | [Handoff](../handoff/subject08_handoff.md) |

---

## 5. 검수 기준과 결과

### 상태와 REVIEW

| 상태 | 뜻 |
|---|---|
| 검수 전 | 아직 보지 않음 |
| 검수 완료 | 확인했고 원본 그대로 둠 |
| 수정 완료 | 원본과 달라지게 고쳤음 |
| 수정 필요 | 판단이 필요함. REVIEW 는 `상태 = 수정 필요` + `발견된 문제 = REVIEW: 이유 코드` |
| 제외 | 최종본에서 뺌 |

- 검수를 마쳤는지는 **검수자 칸**으로 확인한다. (`Enter` 로 저장하면 원본과 달라진 사진은 `수정 완료` 로 기록되므로, 작성자가 이미 고친 사진도 `수정 완료` 가 된다)
- 작성자와 검수자는 서로 달라야 한다.
- 판단하기 어려운 BBox 는 임의로 그리지 않고 REVIEW 로 남긴다. (예: `too_small_to_identify`, `class_ambiguous`) 자세한 기준은 [BBox 기준서](bbox_guide.md) · [Class 기준서](class_guide.md)
- REVIEW 최종 판단: 팀장 + 검수자 【기입】

### 교차검수 분담 (실제)

| 검수자 | 검수한 번호 | 장수 | 위치 | 작성자 (이 범위의 원래 작업자) |
|---|---|---:|---|---|
| 김동훈 | 1 ~ 300 | 300 | 학습데이터1 / train | 이후영 120 · 손상우 128 · 강동연 52 |
| 이후영 | 301 ~ 500 | 200 | 학습데이터1 / train | 손상우 60 · 지혜성 140 |
| 김동훈 | 501 ~ 550 | 50 | 학습데이터2 / train | 김석범 50 |
| 지혜성 | 551 ~ 600 | 50 | 학습데이터2 / train | 김석범 50 |
| 지혜성 | 601 ~ 900 | 300 | 학습데이터2 / train 120 + validation 180 | 김석범 120 · 김동훈 180 |

- 처음에는 5명이 180장씩 맡아 옆 사람이 검수하는 순환 방식을 생각했으나, 검수에 참여한 3명(이후영 · 지혜성 · 김동훈)이 위처럼 나눠서 진행했다. 모든 범위는 검수자 본인이 작성한 사진이 없는 곳이다. 자세한 내용: [검수 배정](../team/검수_배정.md)
- 검수자 합계: 김동훈 350 · 이후영 200 · 지혜성 350. 이름은 검수표 `검수자` 칸 기준이다.

### 검수 결과

| 항목 | 결과 |
|---|---|
| 상태 | 검수 완료 674 · 수정 완료 226 (검수 전 · 수정 필요 · 제외 0) |
| BBox | 원본 4399 → 최종 4561 (추가 166 · 수정 173 · 삭제 4) |
| 라벨이 원본과 달라진 사진 | 235장 |
| 가장 많이 보강된 Class | 병해·갈변(Class 5): 313 → 416 |
| 이미지 유형 | 김치+대상 객체 749 · 대상 객체 단독 150 · 판단 어려움 1 (정상 김치 0) |

---

## 6. 도구와 환경

- 환경: Python 3.14 · Tkinter · Pillow · PyYAML (`requirements.txt`, 폴더 끌어놓기용 `tkinterdnd2` 는 선택). 실행은 `python main.py`
- 규모(2026-10-08 `main` 기준): `src/` 약 4,300줄 · `tools/` 약 2,000줄 · `tests/` 약 5,200줄 · 문서와 보고서 약 3,900줄. 시험 파일 30개가 모두 통과한다 (`python tests/run_all.py`)

| 도구 | 하는 일 |
|---|---|
| `main.py` (`src/`) | 라벨링 프로그램: 이동 · Zoom/Pan · BBox 편집 · Undo · RAW 와 Diff · 상태 필터 · 한 키 검수 · Validation · 검수표 자동 기록 |
| `tools/import_labels.py` | 팀원 라벨(TXT)을 `data/work` 로 가져오기 (`--overwrite` 와 자동 백업) |
| `tools/merge_manifests.py` | 팀원들의 검수표(CSV)를 하나로 합치기 (충돌 규칙, 자동 백업, 출처 바로잡기) |
| `tools/pack_results.py` | 내 범위의 라벨과 검수표를 zip 하나로 묶기 |
| `tools/share_server.py` | 같은 와이파이 안에서 결과 zip 을 내려받고 올리는 임시 서버 (4자리 PIN, 사설 IP 만, 검수자·PM 가이드 탭) |
| `tools/build_final.py` | 검수 끝난 사진·라벨을 `data/final` 로 정리 (조건을 채워야만 만든다) |
| `tools/qa_summary.py` · `tools/final_evidence.py` | QA Summary 와 FINAL 데이터 증빙 생성 |
| `tools/export_manifest_xlsx.py` | 검수표를 제출용 엑셀로 내보내기 |

---

## 7. 데이터 보안 기준

- 실제 JPG·TXT 데이터와 FINAL 데이터는 **Git 저장소에 올리지 않는다** (`.gitignore` 로 제외). 실제 사진·라벨·검수표 내용은 지금까지 푸시된 어느 커밋에도 올라간 적이 없다
- 데이터는 개인 클라우드, 메신저, 공개 파일공유로 보내지 않는다
- 검수 결과(라벨 txt · 검수표)는 같은 와이파이 안에서만 열리는 **근거리 공유 서버**(`tools/share_server.py`)로 주고받는다. 4자리 PIN 이 있고 사설 IP 에서만 접속된다. ([결과 주고받기](../team/결과_주고받기.md))
- 실제 데이터를 캡처한 화면을 문서에 넣을 때는 공개 저장소에 올리지 않는다. 문서의 예시 이미지·파일명은 가짜 샘플이다
- **검수 기록이 쌓이는 검수표(`manifests/dataset_manifest.csv`)도 올리지 않는다.** 실제 사진 파일명이 들어 있어 회사 데이터로 본다. (프로그램이 저장할 때 만들고 `.gitignore` 로 제외) 엑셀 틀(`dataset_manifest.xlsx`)에 실제 기록을 적었다면 그 파일도 올리지 않는다
- Git 에 올리는 것: 소스코드, `requirements.txt`, `configs/classes.yaml`, 문서, 빈 검수표 틀(`dataset_manifest.xlsx`), 보고서
- 공개 저장소에 올라가는 문서에서 실제 사진 파일명을 확인해 가짜 이름으로 바꿨다. (과거 커밋에는 1개가 남아 있다)

---

## 8. Git 기준

```text
기능 하나 구현 → 직접 실행 → 정상 동작 확인 → Commit → 다음 기능 개발
```

- 커밋 메시지: `feat:` 기능 / `fix:` 오류 수정 / `docs:` 문서 / `test:` 시험 / `chore:` 설정 / `perf:` 성능 + 한글 설명
- `update`, `수정`, `최종` 처럼 무엇을 바꿨는지 알 수 없는 메시지는 쓰지 않는다
- **브랜치와 병합 방식**: 각자 자기 이름 브랜치(`feature/이름`)에서 작업하고 푸시한다. **`main` 병합은 PM 강동연이 한다.** `main` 에는 직접 커밋하지 않고, 병합은 `--no-ff` 로 이력을 남긴다. 병합 전에 전체 시험(`python tests/run_all.py`)을 돌린다
- 현재 브랜치: `main` · `feature/ariuck`(강동연) · `feature/huyoung`(이후영) · `feature/seokbeom`(김석범) · `feature/donghun`(김동훈) · `feat/hyesung`(지혜성)

| 항목 | 값 (2026-10-08, `main`) |
|---|---|
| 전체 커밋 | 184개 (병합 49개 포함) |
| 종류 (병합 제외 135개) | feat 63 · docs 42 · fix 16 · test 6 · chore 5 · perf 1 |
| 계정별 커밋 | `ariuck` 169 · `Hyesung` 8 · `ccbb1296` 3 · `tjrqja021206` 3 · `Hu250506` 1 |

예:

```text
feat: 이미지 불러오기 기능 구현
feat: BBox 추가 기능 구현
fix: BBox 저장 위치 오류 수정
docs: 검수 배정을 실제 분담으로 갱신
```

---

## 9. 문서 체계

문서는 일차별이 아니라 **주제별 폴더**로 정리하고, 기준은 `docs/standards/` 한 곳에서만 고칩니다. (목차: [docs/README.md](../README.md))

| 폴더 | 내용 |
|---|---|
| `docs/standards/` | 기준서: 이 문서, Class · BBox · 검수표 작성 |
| `docs/design/` | 필수 기능, 화면 설계, 의사코드, End-to-End 계획 |
| `docs/team/` | 역할 분담, Gate 체크리스트, 라벨 합치기, 결과 주고받기, 검수 배정 |
| `docs/handoff/` | 교과 8 Handoff |
| `docs/records/`, `docs/meetings/` | 과정 기록, 산출물 요약, 회의록(1~3일차) |
| `reports/` | QA Summary, FINAL 증빙, Test Report |

---

## 10. 완료 기준과 달성 현황

| 완료 기준 | 결과 (2026-10-08) |
|---|---|
| 미처리 REVIEW 0건 | **달성** — 0건 |
| Validation 오류 0건 | **달성** — CRITICAL · WARNING · INFO 모두 0건 (작은 점 박스 1개를 확인 후 삭제해 TINY_BOX 경고도 해소) |
| 이미지와 TXT Pair 확인 완료 | **달성** — 900 / 900 |
| 900장 전체 검수 완료 | **달성** — 검수자 칸 900줄 모두 기록, 작성자와 검수자가 같은 줄 0 |
| FINAL 데이터 정리 완료 | **달성** — `data/final/` 이미지 900장 + 라벨 900개 (`tools/build_final.py`) |
| 교과 8 사용 가능 | **달성** — [QA Summary](../../reports/qa_summary.md) 최종 판정, [Handoff](../handoff/subject08_handoff.md) 최소 확인 8항목 통과 |

> 숫자는 검수표와 `data/work` 를 읽어 센 값이다. 라벨을 더 고치면 `python tools/build_final.py --apply --overwrite` 로 최종본을, `python tools/qa_summary.py --apply` 로 QA Summary 를 다시 만든다.

---

## 11. 남은 일 · 사람이 확인할 것

| 항목 | 내용 |
|---|---|
| 캡처·영상 | 폴더 구조·이미지 수량·TXT 수량 캡처, 대표 검수 완료 이미지 3~5장, 프로그램 실행 화면 2~3장, 짧은 시연 영상. 실제 사진이 나오므로 외부에 공유하지 않는다 (NDA) |
| `【기입】` 칸 | REVIEW 최종 판단자, 회의 일시·장소·참석, Pilot Test 일시·시험자, 인계 일시·받는 사람, 손상우 역할 표기 |
| `【확인 필요】` | 계정과 이름 짝, Figma 보드의 역할·분담 표기와의 일치 |
| 검수표의 `위치 맞음`·`Class 맞음`·`누락 객체 여부` | 900줄 모두 비어 있음. 검수 상태로 갈음했으며, 채울지는 팀이 정한다 |
| 푸시 | `main` 과 `feature/ariuck` 을 GitHub 에 푸시 (VS Code). 올리기 전에 저장소 공개 범위와 문서 속 회사 데이터 설명을 확인한다 |

---

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-10-06 | 최초 작성 (공통 데이터·팀 작업·보안·Git·완료 기준) | 1일차 기준선 |
| 2026-10-07 | 검수 담당 범위·교차검수 분담을 실제 분담으로 갱신, 근거리 공유 서버 추가 | 4일차 검수 작업 |
| 2026-10-08 | 프로젝트 개요, 산출물 우선순위, 팀원 6명 역할·기여, 단계별 진행, 도구, Git 현황, 달성 현황을 추가해 전체 정리 | 제출용 정리 |
