# Project Baseline

> 우리 팀이 교과 7 프로젝트(조각김치 이물검출 라벨링)를 **어떤 기준으로 진행하는지** 정한 공통 규칙입니다.
> `【기입】` 은 팀이 정해서 채우는 칸입니다. (임의로 채우지 않습니다)

## 1. 공통 데이터 기준

- 전체 이미지: 900장 (JPG) + YOLO TXT 900개
  - 이물검출_학습데이터1 / train: 500 · 이물검출_학습데이터2 / train: 220 · 이물검출_학습데이터2 / validation: 180
- Label Format: YOLO Detection TXT (`class_id x_center y_center width height`, 0~1 비율값)
- Class: 0~6 (회사 제공 번호 그대로, 재번호 금지) — 설정 파일 `configs/classes.yaml`
- Class 4(고무장갑): 사용하지 않음 (발견 시 삭제하지 않고 REVIEW)
- 기존 `train / validation` 구분과 데이터셋 출처는 **유지**한다 (섞거나 합치지 않음)
- RAW 데이터 수정 금지

## 2. 우리 팀 작업 기준

- 팀원: 5명 — 강동연 · 김석범 · 김동훈 · 이후영 · 지혜성
- 1차 작업(라벨 검수): 각자 180장 담당

| 담당 | 번호 | 범위 | 장수 |
|---|---|---|---:|
| 【기입】 | 1~180 | 이물검출_학습데이터1 / train | 180 |
| 【기입】 | 181~360 | 이물검출_학습데이터1 / train | 180 |
| 【기입】 | 361~540 | 학습데이터1 / train 140장 + 학습데이터2 / train 40장 | 180 |
| 【기입】 | 541~720 | 이물검출_학습데이터2 / train | 180 |
| 【기입】 | 721~900 | 이물검출_학습데이터2 / validation | 180 |

- 교차검수: 옆 사람이 검수 (1→2→3→4→5→1 순환), 작업자와 검수자는 서로 달라야 함
- REVIEW 최종 판단: 팀장 + 검수자 【기입】
- 작업 중 데이터 저장 위치: `data/work/` (RAW 와 같은 폴더 구조)
- 최종 QA 완료 데이터 저장 위치: `data/final/`
- 작업 상태 기록: `manifests/dataset_manifest.xlsx` (작성 방법 [manifest_guide.md](manifest_guide.md))

### 역할 분담

| 역할 | 책임 | 담당 |
|---|---|---|
| PM / 문서 | 기준선·일정, Git 병합, 문서와 교과 8 인계 | 강동연 |
| GUI / 이미지 | 화면, 이미지 표시, 이전/다음, Zoom/Pan | 이후영 |
| BBox / 좌표 | BBox 추가·수정·삭제, 화면↔원본 좌표 | 김석범 |
| 라벨 저장 / 데이터 | Class, TXT Load/Save, Manifest, RAW/WORK 관리 | 김동훈 |
| QA / 검증 | Validation, Golden/Pilot 시험, 이슈 기록 | 지혜성 |

> 2일차 구현은 이 역할대로 진행했다: 이동(이후영) · Zoom/Pan(김석범) · 저장·상태(김동훈) · Validation·시험(지혜성) · 병합·문서(강동연).

## 3. 데이터 보안 기준

- 실제 JPG·TXT 데이터와 FINAL 데이터는 **Git 저장소에 올리지 않는다** (`.gitignore` 로 제외)
- 데이터는 개인 클라우드, 메신저, 공개 파일공유로 보내지 않는다
- 실제 데이터를 캡처한 화면을 문서에 넣을 때는 공개 저장소에 올리지 않는다
- **검수 기록이 쌓이는 검수표(`manifests/dataset_manifest.csv`)도 올리지 않는다.** 실제 사진 파일명이 들어 있어 회사 데이터로 본다. (프로그램이 저장할 때 만들고 `.gitignore` 로 제외)
  엑셀 틀(`dataset_manifest.xlsx`)에 실제 기록을 적었다면 그 파일도 올리지 않는다.
- Git 에 올리는 것: 소스코드, `requirements.txt`, `configs/classes.yaml`, 문서, 빈 검수표 틀(`dataset_manifest.xlsx`), 보고서

## 4. Git 기준

```text
기능 하나 구현
→ 직접 실행
→ 정상 동작 확인
→ Commit
→ 다음 기능 개발
```

- 커밋 메시지: `feat:` 기능 / `fix:` 오류 수정 / `docs:` 문서 / `test:` 시험 / `chore:` 설정
- `update`, `수정`, `최종` 처럼 무엇을 바꿨는지 알 수 없는 메시지는 쓰지 않는다
- 브랜치와 병합 방식: 각자 자기 이름 브랜치(`feature/이름`)에서 작업하고 푸시한다. `main` 병합은 PM(강동연)이 한다. `main` 에는 직접 커밋하지 않는다.

예:

```text
feat: 이미지 불러오기 기능 구현
feat: BBox 추가 기능 구현
feat: YOLO TXT 저장 기능 구현
fix: BBox 저장 위치 오류 수정
```

## 5. 완료 기준

- 미처리 REVIEW: 0건 (검수표에서 `상태 = 수정 필요` 이면서 `발견된 문제`가 `REVIEW` 로 시작하는 행이 없음)
- Validation 오류: 0건
- 이미지와 TXT Pair 확인 완료
- 900장 전체 검수 완료
- FINAL 데이터 정리 완료
