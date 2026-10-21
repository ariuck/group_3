# 3조 발표자료 — 조각김치 이물검출 (교과 7 + 교과 8)

[전체 프로젝트](../README.md) · [교과 7](../subject7/README.md) · [교과 8](../subject8/README.md)

이 폴더는 프로젝트의 통합 발표 결과물입니다. 저장소의 **`presentation/`를 원본으로 수정**하고, 별도 사본과 내용을 섞지 않습니다.
현재 판: **2026-10-21 · 본편 17장 (시연영상 2개 포함) + 부록 A0~A18** · 말하는 시간 13:05 + 교대 5회 ≈ **13:30** (15분 제한).

## 파일

| 용도 | 경로 |
|---|---|
| 발표 화면 (원본) | `index.html`, `assets/` (CSS · 연결 스크립트 · 그래프 · 자막) |
| 발표 대본 | `발표대본.html` (담당자별 보기 · 인쇄), 데이터 `assets/speaker_script.json` |
| 진행표 | `발표진행표.md` (순서 · 시간 · 인계 문장 · 질문 담당) |
| 시연영상 | `private/videos/subject7_labeling_20261021.mp4` (6번, 65.7초) · `private/videos/화면 녹화 중 2026-10-21 102056.mp4` (15번, 49초) |
| 영상 자막 | `assets/video1_labeling.vtt` · `assets/video2_final.vtt` |
| 실제 사진 | `private/photos/` |
| 발표 서버 | `발표서버 시작.bat` → `start_presentation.ps1` → `serve_deck.py` |
| 이전 판 | `backup/` (Git) · `private/archive/` · `private/backups/` |
| 생성 스크립트 | `private/tools/` (대본 → 노트·대본 페이지 재생성 등, Git 제외) |
| 과거 기획문서 | `private/planning/` (현행 내용의 기준으로 쓰지 않음) |

`private/` 전체(사진 · 영상 · 스크립트 · 과거 자료)는 Git 에 올라가지 않습니다 (`.gitignore`).
팀원은 `git pull` 뒤 **사진과 영상을 파일저장소/USB 로 받아 `private/photos/`, `private/videos/` 에 넣어야** 화면이 다 보입니다. 영상 파일 이름은 바꾸지 않습니다.

## 실행과 발표

1. `발표서버 시작.bat` 실행 (Windows Python 3 필요). 발표 서버(8765)와 시연 GUI 서버(8010, `subject8/app/server.py`)를 함께 켭니다. 실행 로그 `private/runtime/`.
2. `http://127.0.0.1:8765/index.html#1` 을 열고 `F` 전체화면.
3. 같은 네트워크의 팀원은 창에 표시된 `http://<이 PC IP>:8765/index.html#1` 로 봅니다 (IP 는 바뀔 수 있음, 서버 PC 가 켜져 있는 동안만).
4. 서버 없이 `index.html` 을 더블클릭해도 영상과 한국어 자막이 표시됩니다. 파일로 열 때는 HTML에 내장된 자막을 사용하고, 서버 주소에서는 `assets/`의 VTT 파일을 사용합니다. 라이브 GUI는 서버 실행이 필요합니다.

영상 장(6 · 15번)은 들어가면 자동 재생됩니다. 클릭 또는 `P` 로 멈춤/재생. 라이브 GUI 시연은 본편에서 하지 않고, 질문이 나오면 부록 **A13** 에서 엽니다.

## 조작

| 키 | 동작 |
|---|---|
| ← → / Space / PgUp·PgDn | 이전 · 다음 (클리커 가능) |
| F | 전체화면 |
| S · T | 발표자 노트 · 노트 타이머 |
| O | 슬라이드 목록 (본편 + 부록) |
| B | 화면 검게 (Q&A 대기) |
| P | 영상 멈춤/재생 |
| L · M · ? | 포인터 · 효과 끄기/켜기 · 도움말 |
| 주소 `#7`, `#a3` | 해당 슬라이드로 이동 · Backspace 로 부록 → 본편 |

## 본편 구성

| # | 발표 | 슬라이드 |
|---:|---|---|
| 1–2 | 강동연 | 표지 · 라벨 품질이 성능의 상한 |
| 3–4 | 이후영 | 데이터 구성 · 자체 개발 라벨링 도구 |
| 5–6 | 김석범 | 전수 교차검수 결과 · ▶ 시연 1 라벨링 도구 |
| 7–9 | 손상우 | 데이터 분할 정책 · Baseline 한계 · 데이터 누수 재분할 |
| 10–12 | 김동훈 | 개선 실험 · Baseline vs Final · 소형 객체 Recall |
| 13–17 | 지혜성 | Frozen Test 0.639 · 한계 · ▶ 시연 2 Final Model 검사·보고서 · 후속 과제 · 요약 |

화면 문구는 개조식(명사형), 말하는 문장은 발표자 노트와 `발표대본.html` 에만 둡니다.
부록 (주제별, **A0 목차**에서 클릭 이동 · `O` 목록도 그룹별):

| 그룹 | 부록 |
|---|---|
| 교과 7 · 데이터 | A1 원본·작업본·최종본 · A2 교과 7→8 연결 |
| 데이터 분할 | A3 v5 분할표 · A4 분할·라벨 변경 이력 |
| 학습 · 개선 실험 | A5 학습 설정 · A6 실험 전표 · A7 Class별 성능 · A8 해상도·학습 비용 · A9 4라운드·Final 선택 규칙 |
| 평가 · 최종 모델 | A10 평가 방식 · A11 Frozen Test 상세 · A12 confidence 기준별 박스 판정 · A13 라이브 GUI 시연 절차 |
| Final 뒤 진단 (exp063) | A14 exp063 갈변 진단 요약 · A15 다른 Class 하락 분석 |
| 운영 · 예상 질문 | A16 재현성 · 보안 · A17 예상 질문 34개 |
| 지표 읽는 법 | A18 mAP 계산 — IoU 합격선과 confidence 순서 (슬라이더로 직접 움직여 보기, 질문 대응용) |

## 함께 수정하기 (Git)

```bash
cd ~/group_3 && git pull origin main          # 고치기 전에 항상 최신으로
# presentation/index.html 수정 → 서버 주소로 열어 확인
git add presentation && git status --short   # .jpg · .mp4 · private/ 가 없어야 함
git commit -m "docs(presentation): <슬라이드 번호> <바꾼 것>" && git push origin main
```

- `index.html` 한 파일을 여럿이 고치므로 **고치기 직전에 pull, 끝나면 바로 push**. 같은 슬라이드를 두 명이 동시에 고치지 않습니다.
- 대본을 고칠 때는 `assets/speaker_script.json` 을 고친 뒤 `private/tools/` 의 스크립트로 노트와 `발표대본.html` 을 다시 만듭니다 (또는 정리 담당에게 요청).
- 숫자를 바꿀 때는 아래 대조표의 저장소 파일에서 확인합니다.

## 사진 사용 기준

원본 사진은 포트폴리오 · 내부 발표에 사용할 수 있습니다. 이물이 보이는 원본 사진·영상은 **GitHub 같은 공개 저장소에 올리지 않습니다**. 라벨 · 텍스트 · 파일명은 같은 금지 대상이 아닙니다.

| 사진·영상 슬롯 | 쓰는 곳 |
|---|---|
| `private/photos/s04_tool_real.jpg` | 4 — 없으면 `assets/ui_main.png`(샘플 화면)로 대체 |
| `private/photos/s08_fn.jpg` | 8 — Baseline 이 놓친 사례 |
| `private/photos/s09_g00_sheet.jpg` | 9 — 촬영 묶음 G00 사진판 |
| `private/photos/s08_c5_train_vs_val.jpg` | 14 — 갈변 Train vs Val |
| `private/photos/s15_detect_1~3.jpg` · `s16_gui_preview.png` | A13 — Final 비교 사진 · GUI 캡처 |
| `private/videos/` 영상 2개 | 6 · 15 |

## 숫자 → 근거 (저장소 `subject8/` · `subject7/` 파일)

| 슬라이드 | 숫자 | 근거 |
|---|---|---|
| 3 · 5 | 900장 · 6 Class · BBox 4,399 → 4,561 · 235장(26.1%) · 추가 166 · 수정 173 · 삭제 4 | subject7 `qa_summary` |
| 4 | 저장·재로드 900/900 일치 | subject7 `test_report` |
| 7 | Train 558 · Val 104 · Test 82 · Bridge 156 · Class당 BBox ≥ 15 · G00~G17 | `docs/project/kimchi_v5_split.md`, `split_policy.md` (부록 A3) |
| 8 | Baseline P 0.888 · R 0.589 · mAP50-95 0.470 | `reports/runs_summary.csv` |
| 9 | 동일 촬영 묶음 63% (83/132) → 6% (6/104) | `reports/01_data/leakage_check.csv` |
| 10 | 0.470 · 0.646 · 0.704 · A 0.715 · C 0.730 · B 0.739 (0.726~0.749) · 채택 기준 +0.02 · exp050 | `experiment_log.csv`, `final_model_selection.md` |
| 11 | P 0.888→0.945 · R 0.589→0.822 · mAP50 0.688→0.840 · mAP50-95 0.470→0.749 · Test 0.868 / 0.744 / 0.726 / 0.639 · TP 395→506 · FN 111→34 | `runs_summary.csv`, `05_final/final_metrics.csv`, `03_failure_analysis/*_summary.csv` |
| 12 | 소형 플라스틱·돌 Recall 0.613→0.969 · Class 오분류 35→1 · 소형 갈변 2/15 | `03_failure_analysis/*_recall_by_size.csv`, `*_summary.csv` |
| 13 | Val 0.749 → Frozen Test 0.639 · Class별 Val/Test | `05_final/final_metrics.csv`, `final_class_metrics.csv` |
| 14 | 갈변 Test Recall 0 · Val 갈변 BBox 15개 | `final_model_selection.md` |
| 15 | conf 0.25: TP 506 · FP 31 · FN 34 · 0.50: 500 · 12 · 41 · 0.45: 503 · 15 · 38 · 93.0% / 97.1% · 37ms | 시연 보고서 (2026-10-21 10:15), `subject8/app/report.py` |
| 16 | Bridge Holdout 156장 | `docs/project/handoff/subject14_handoff.md` |

계산·표기 메모: Baseline mAP50 원값 0.6875 → 0.688, mAP50-95 0.4695 → 0.470 · 타일링 실험(exp004·010)은 원본 단위 채점값만 사용.

## 발표 전에 팀이 확인할 것

- [ ] 각자 첫 문장(역할 소개)이 사실과 맞는지 — 특히 7번 손상우 · 10번 김동훈
- [ ] 사진 · 영상을 받아 `private/` 에 넣고 6 · 15번 영상과 자막 재생 확인
- [ ] Val 0.749 → Test 0.639 질문 답변(부록 A17 Q26~28)을 6명이 같은 말로
- [ ] 전체 리허설 1회 — 목표 13:30, 실제 시간 기록
