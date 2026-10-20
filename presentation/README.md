# 3조 발표자료 (교과 7 + 교과 8)

`index.html` 하나로 동작합니다. 인터넷이 없어도 열리고, 외부 요청은 0개입니다.
**2026-10-20 개정**: Final Model(exp050) · Frozen Test 1회(0.639) 반영 — 본편 16 → 17장, 부록 A9 추가. 10-19 판은 `backup/index_2026-10-19.html`.

## 여는 법
- `index.html` 을 더블클릭해 브라우저(Chrome·Edge)로 엽니다. `F` 키로 전체화면.
- 사진은 `private/photos/` 의 파일을 참조만 합니다. 파일이 없으면 회색 `[사진 자리]` 박스가 보입니다.
- **이 폴더는 Git 에 있습니다** (저장소 맨 위 `presentation/`). 교과 7 + 교과 8 공동 발표라서 2026-10-20 에 `subject8/presentation/` 에서 **`presentation/` 으로 옮겼습니다** (파일 이력은 그대로 이어짐). 단 **`private/`(실제 사진) · PDF · 영상은 Git 에 없습니다** — 이 폴더의 `.gitignore` 와 저장소 `*.jpg` 규칙이 막는다.
- 사진이 보이게 하려면 원본 PC 에서 USB 로 `private/photos/` 를 받아 **각자 이 폴더 안에** 넣습니다 (`presentation/private/photos/`). Git 이 무시하므로 커밋되지 않습니다. 절대 `git add -f` 하지 않기. 옛 위치 `subject8/presentation/private/` 에 사진을 넣어 둔 PC 는 **`presentation/private/` 로 옮기세요** (옛 폴더는 이 이동 뒤에 비어서 남습니다).
- 아래 "숫자 → 근거 대조표"의 파일 이름(`final_model_selection.md`, `experiment_log.csv` 등)은 **`subject8/` 안의 파일**입니다.

## 함께 수정하기 (Git)

```bash
cd ~/group_3 && git pull origin main          # 고치기 전에 항상 최신으로
# presentation/index.html 수정 → 브라우저로 열어 확인
git add presentation && git status --short   # .jpg · .mp4 · private/ 가 없어야 함
git commit -m "docs(presentation): <슬라이드 번호> <바꾼 것>" && git push origin main
```

- `index.html` 한 파일을 여럿이 고치므로 **고치기 직전에 pull, 끝나면 바로 push** — 같은 슬라이드를 두 명이 동시에 고치지 않도록 담당 슬라이드(아래 "본편 구성")만 고친다.
- 숫자를 바꿀 때는 아래 "숫자 → 근거 대조표" 의 저장소 파일에서 확인하고, 표도 같이 고친다.
- 충돌이 나면 혼자 해결하지 말고 정리 담당에게 알린다.

## 조작
| 키 | 동작 |
|---|---|
| ← → / Space / PgUp·PgDn | 이전·다음 (클리커 가능) |
| F | 전체화면 |
| S | 발표자 노트 (발표자 · 목표 시간 · 대본 · 넘기는 문장 · 시연 절차) |
| T | 노트의 경과 타이머 시작/초기화 |
| O | 슬라이드 목록 (본편 + 부록 썸네일) |
| B | 화면 검게 (Q&A 대기) |
| Home / End | 처음 / 끝 |
| 주소 `#9`, `#a4` | 해당 슬라이드로 바로 이동 (부록 A1~A9) |
| Backspace | 부록에서 본편으로 돌아가기 |
| ↑ ↓ / 마우스 휠 | A1 실험 전표 · A8 예상 질문 스크롤 |

PDF 백업: 브라우저 인쇄(Ctrl+P) → 대상 "PDF로 저장" → 배경 그래픽 켜기. 슬라이드당 1페이지(본편 17 + 부록 9).

## 본편 구성 (10-20)
| # | 발표자 | 슬라이드 | 초 |
|---|---|---|---:|
| 1 · 2 | 강동연 | 표지 · 문제 정의 | 20 · 40 |
| 3 · 4 | 이후영 | 데이터 · 라벨링 도구(시연 ①) | 50 · 50 |
| 5 · 6 · 7 | 지혜성 | 생명주기 · QA 결과 · 현재 위치 | 50 · 50 · 30 |
| 8 · 9 | 김동훈 | Baseline · v4 누수 → v5 | 65 · 90 |
| 10 · 11 | 손상우 | 개선 실험 0.470 → 0.739 · **Final을 고른 규칙 (신규)** | 60 · 35 |
| 12 · 13 · 14 | 김석범 | 인사이트 · **Frozen Test 0.639 (신규)** · 한계 | 40 · 50 · 50 |
| 15 | 손상우 | [라이브] Final 검출 시연 ② | 85 |
| 16 | 강동연 | 다음 단계 · 교과 14 인계 | 30 |
| 17 | 전원 | Q&A | — |

말하는 시간 합 13:15 + 전환 7회 × 10초 = **약 14:25** (15분 중 여유 0:35). 옛 13 "3대 분산 실험"은 새 11 "Final을 고른 규칙"으로 바뀜.

## 사진 슬롯 (`private/photos/`)
| 슬롯 | 슬라이드 | 상태 |
|---|---|---|
| `s04_tool_real.jpg` | 4 | 없음 → `assets/ui_main.png`(가짜 샘플 화면)으로 대체 표시. 도구를 실제 사진으로 띄워 캡처해 넣으면 교체됨 |
| `s08_fn.jpg` · `s08_fp_background.jpg` · `s08_class_error.jpg` | 8 | 있음 — Baseline 실패 사례 |
| `s08_c5_train_vs_val.jpg` | 14 | 있음 — 갈변 Train vs Val |
| `s09_g00_sheet.jpg` | 9 | 있음 — G00 촬영 순서 사진판 |
| `s09_g17_sheet.jpg` | (예비) | 있음 |
| `s15_detect_1~3.jpg` | 15 | 있음 (10-20) — Final(exp050, imgsz 2240, conf 0.25)로 10-19 와 같은 Val 사진 3장 (`250424_143312128093` · `250411_095845387065` · `250424_143017228317`), `runs/predict/g3pres_final_d1~3`. exp063 학습 중이라 CPU 로 예측. 옛 `s14_detect_1~3.jpg` 는 exp007 결과라 슬라이드에서 빠짐 |
| `s15_backup.mp4` | 15 | **없음 → 시연 ② 화면 녹화해서 넣기** |

`assets/` 추가(10-20, 그래프라 사진 없음): `final_test_confusion_matrix_normalized.png`(A9) · `final_test_pr_curve.png`(예비).

## 숫자 → 근거 대조표
근거는 저장소 `origin/main` `1b5c354` 의 원본 파일 (소스 절 번호는 발표 준비 메모 `01_source_facts.md` 기준 — 이 메모는 저장소에 없음).

| 슬라이드 | 숫자 | 소스 절 | 저장소 확인 |
|---|---|---|---|
| 1, 3 | 900장 · 4K 4848×2704 · 6 Class | 1, 2.2 | — |
| 2 | 원본 4,399박스 | 2.6 | subject7 qa_summary |
| 3 | Class별 727 · 1,852 · 932 · 379 · 416 · 255, 갈변 313→416 (+103) | 2.3, 5.4 | subject7 qa_summary |
| 4 | Round-trip 900/900, 최대 오차 5e-11 | 2.5 | subject7 test_report |
| 6 | 900/900 · 교차검수 100% · 235장(26.1%) · 추가 166·수정 173·삭제 4 · 이슈 28 | 2.6 | subject7 qa_summary |
| 7 | 10-20 Final · Frozen Test 0.639, exp026·027 재학습 완료 · 5라운드 exp063 1회 | 1.1, 3.1 | final_model_selection.md |
| 8 | P 0.888 · R 0.589 · mAP50-95 0.470, 실패 233 | 3.6, 3.7 | runs_summary.csv |
| 9 | 63% (83/132) → 6% (6/104), Train 558 · Val 104 · Test 82 · Bridge 156 | 3.3, 3.4 | — |
| 10 | 0.470 · 0.646 · 0.704 · A 0.715(0.707~0.724) · C 0.730 · **B 0.739 (0.726~0.749)** · 62분 · 기각 +0.003 · −0.006 · −0.008 · −0.044 | 3.8, 3.8.1, 5.7 | experiment_log.csv, runs_summary.csv, final_model_selection.md |
| 11 | 규칙 커밋 10-19 16:55(`f8b60cd`, seed 5개로 확정 · 16:42 `eed98b4` 는 seed 3개 버전) · 첫 학습 17:25 · 6방향 평균 0.733 · 0.740 · 0.731 · 0.727 · 0.732 · 0.726, 갈변 0.094~0.111, 채택선 0.759 | 3.10 | experiment_handoff.md 9장, final_model_selection.md |
| 12 | +0.234 · +0.040 · 0.02 · 1280 0.680 / 1920 0.715 / 2240 0.739 / 2560 0.731 · 예측 2240 0.749 · 2560 0.751 · 2880 0.749 | 3.8 인사이트 8~11 | final_model_selection.md |
| 13 | Val 0.749 → Test 0.639 · P 0.868 · R 0.744 · mAP50 0.726 · Class Val/Test · 기여 0.066 | 3.13, 5.8 | 05_final/final_metrics.csv, final_class_metrics.csv |
| 14 | 갈변 Val 0.115 · Test Recall 0 · 나뭇잎·종이 P 0.367 R 0.855 (23박스) · 반점 Train 20→8 · Val 41→15 · Test 14→14 | 3.9, 9.7 | final_model_selection.md, experiment_handoff.md 9장 |
| 15 | imgsz 2240 · conf 0.25 · 약 37ms/장 · Test 0.639 | 1.2, 3.13 | models/README.md |
| 16 | Bridge 156장 | 3.4, 3.11 | — |
| A1 | 0~3라운드 + B 실행별 P·R·mAP, 학습 86·89·169·18·62분 | 3.8, 3.8.1 | runs_summary.csv, experiment_log.csv |
| A4 | Final 11s · 2240/2 · seed 2 · 62분 · 6.7GB · 해시 `a185c4401ace` | 9.1, 3.13 | final_model_selection.md |
| A5 | seed 반복, 선택 편향 → Test 0.639 | 9.2 | — |
| A8 | 질문 24 + 25(Pilot) + 26~29(Final·Test) | 9.8 | — |
| A9 | Class별 Val/Test/P/R/박스, 기여 = (Val−Test)÷6 | 3.13 | final_class_metrics.csv |

### 소스와 다르게 쓴 곳 · 계산한 값
- Baseline mAP50: 원값 0.6875 라 **0.688**. v5 Baseline mAP50-95 원값 0.4695 → **0.470** (선택 문서는 0.469).
- exp004·exp010 은 원본 단위 채점값(*)만 사용.
- **Class 기여(0.066 등)는 저장소 숫자로 계산한 값** — (Val − Test) ÷ 6. 저장소 문서에 직접 있는 숫자는 아님.

## 발표 전에 팀이 확인할 것
- [ ] 발표 일시·장소 (표지 `TBD`)
- [ ] 발표자 배정 (10-20 개정: 손상우 10·11·15, 김석범 12·13·14) — 본인 확인
- [ ] **Val 0.749 → Test 0.639 답변(Q26~28)을 6명이 같은 말로** — 리허설
- [ ] Q2 갈변 기준 개정 시점 · Q10 배치 기록 사람 검수 · Q23 AI 사용 범위 (A8 `발표 전 확인` 배지)
- [x] `s15_detect_1~3.jpg` Final 로 생성 (10-20) · [ ] `s15_backup.mp4` 녹화, 시연 PC 점검 (`qa_acceptance_check.py`)
- [x] exp026 · 027 결과로 11번 ③ 행 갱신 (10-20: seed 5개 평균 0.731, 결론 그대로)
