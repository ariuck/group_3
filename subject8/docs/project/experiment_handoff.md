# 실험 인수인계 · 3대 분산 학습 계획 (kimchi_v5)

> 작성 2026-10-19 · 정리 담당 ariuck (`feature/ariuck`). 이 문서만 보고 다른 PC 에서 이어서 실험할 수 있게 쓴다.

## 1. 지금까지 (요약)

- **공식 Dataset `kimchi_v5`** — v4 Val 의 누수(132장 중 83장이 Train 과 같은 촬영 묶음)를 없앤 재분할. Train 558 / Val 104 / Test 82 / Bridge 156. 기준 [`kimchi_v5_split.md`](kimchi_v5_split.md)
- **실험 8개** (같은 Val 104장, mAP50-95): baseline 0.470 → 1280 0.646 → 1920 0.704 → **11s·1920·증강(exp007) 0.724 (현재 최고)**. 전체 표·개선점·한계: [`reports/04_improvement/baseline_vs_improved.md`](../../reports/04_improvement/baseline_vs_improved.md), 판정 [`experiment_log.csv`](../../reports/04_improvement/experiment_log.csv), 모델 목록 [`models/README.md`](../../models/README.md)
- **Final Model 은 아직 정하지 않았다.** 아래 분산 실험 결과를 보고 8일차에 Val 근거로 정한다.
- **Frozen Test(G07·G14)·Bridge Holdout 은 쓰지 않는다.** 예측 스크립트도 막혀 있다.

## 2. 3대 분산 계획

모든 실험은 **exp007 (YOLO11s · imgsz 1920 · batch 3 · 증강 flipud 0.5·hsv_v 0.6 · 50 epoch)** 에서 한 변수씩 바꾼다. 조건은 `scripts/11_train_v5.py` 의 `RUNS` · `scripts/14_train_tiles_v5.py` 의 `TILE_EXPS` 에 **이미 다 등록**돼 있어서, 각자 실행만 하면 된다 (코드를 고치지 않으므로 브랜치끼리 충돌하지 않음).

| 담당 · 브랜치 | 실험 | 바꾸는 것 (exp007 대비) | 알고 싶은 것 | 명령 | 예상 시간 (RTX 3060) |
|---|---|---|---|---|---|
| **상우** · `feature/sangwoo` | exp008 | epochs 50 → 100 | exp007 이 50 epoch 에서 아직 오르는 중 → 더 오르나 | `python scripts/11_train_v5.py --run exp008` | 약 1시간 30분 |
| | exp013 | seed 42 → 7 | 같은 조건 반복 시 점수가 얼마나 흔들리나 (0.02 차이가 의미 있나) | `python scripts/11_train_v5.py --run exp013` | 약 45분 |
| **동연** · `feature/dongyeon` | exp010 | 입력: 원본 → 2×2 타일링 | 큰 모델 + 타일링이 작은 이물(갈변·가지)에 더 효과적인가 | `python scripts/14_train_tiles_v5.py --exp exp010` | 약 3시간 |
| **혜성** · `feat/hyesung` | exp009 | YOLO11s → **11m** (batch 2) | 모델을 더 키우면 더 오르나 | `python scripts/11_train_v5.py --run exp009` | 약 1시간 30분~2시간 |
| | exp011 | 증강 끄기 | 11s 에서 증강이 실제로 도움이 되나 (효과 분리) | `python scripts/11_train_v5.py --run exp011` | 약 45분 |
| | exp012 | imgsz 1920 → 1280 (batch 6) | 더 가볍고 빠른 후보 (교과 14 현장용) | `python scripts/11_train_v5.py --run exp012` | 약 25분 |

- 브랜치 이름은 예시다. 이미 쓰던 개인 브랜치가 있으면 그것을 쓰고 이 표만 고친다.
- **GPU 가 가장 큰 PC 가 exp009 (11m) 를 맡는다.** 시작 전에 `nvidia-smi` 로 메모리를 확인하고, 12GB 에서 넘치면(속도가 갑자기 느려짐 · `out of memory`) 멈추고 알려 준다 — batch 1 로 낮추지 않는다 (BatchNorm 이 불안정해짐).
- 한 PC 에서는 **한 번에 하나만** 학습한다 (같이 돌리면 메모리가 넘쳐 꺼진 적 있음). 여러 실험은 한 줄로 이어서: `python scripts/11_train_v5.py --run exp011 && python scripts/11_train_v5.py --run exp012`

## 3. 각 PC 에서 하는 순서

```bash
# 1) 최신 main 받고 자기 브랜치 만들기 (이미 있으면 checkout 후 git merge main)
cd ~/group_3 && git checkout main && git pull
git checkout -b feature/sangwoo            # 혜성: git checkout feat/hyesung && git merge main

# 2) 회사 원본 폴더를 subject7/data/raw/ 에 넣고 (USB — 외부 클라우드·메신저 금지) 올인원 준비
cd subject8 && python3 scripts/00_setup.py   # 마지막에 "같은 데이터 · 같은 분할 ✓" 이면 정상

# 3) 맡은 실험 실행 (위 표의 명령)
.venv/bin/python scripts/11_train_v5.py --run exp008

# 4) 자기 실험 결과만 커밋 → 푸시 (아래 표)
```

### 커밋하는 것 / 하지 않는 것

| 커밋한다 (자기 실험 이름이 들어간 것만) | 커밋하지 않는다 (정리 담당이 합친 뒤 한 번에 만듦 — 브랜치끼리 충돌 방지) |
|---|---|
| `runs/<실행>/` (results.csv · args.yaml · 그래프) | `models/README.md`, `reports/runs_summary.csv`, `reports/figures/` (`plot_runs.py` 결과) |
| `models/improved/<실행>.pt` | `reports/04_improvement/experiment_log.csv` |
| `reports/04_improvement/<실행>_training_condition.md` | `scripts/`, `src/`, `docs/` (고칠 일이 생기면 따로 알려 주기) |
| (동연) `reports/04_improvement/tiling_eval_exp010.csv` | 사진 (`*.jpg`) — `.gitignore` 가 막지만 `git status` 로 한 번 더 확인 |

```bash
cd ~/group_3
git add subject8/runs/exp008_v5_s_imgsz1920_aug_epoch100 \
        subject8/models/improved/exp008_v5_s_imgsz1920_aug_epoch100.pt \
        subject8/reports/04_improvement/exp008_v5_s_imgsz1920_aug_epoch100_training_condition.md
git status                                  # 위 파일만 초록색인지 확인
git commit -m "feat(subject8): exp008 v5 11s 1920 증강 epoch100 — Val mAP50-95 0.xxx"
git push -u origin feature/sangwoo
```

커밋 메시지나 PR 설명에 **best epoch 의 Val mAP50-95 · 학습 시간 · 특이사항(메모리 넘침 등)** 을 적어 준다. 끝나면 GitHub 에서 main 으로 PR 을 열거나 정리 담당에게 알려 준다.

## 4. 정리 담당이 합칠 때 (ariuck)

```bash
cd ~/group_3 && git checkout feature/ariuck && git fetch origin
git merge origin/feature/sangwoo origin/feature/dongyeon origin/feat/hyesung   # 실행 이름이 달라 충돌 없음
cd subject8 && .venv/bin/python scripts/plot_runs.py                          # 그래프 · runs_summary · models/README
# experiment_log.csv 에 실험별 한 줄 + 판정, baseline_vs_improved.md 표·개선점 갱신
.venv/bin/python ../subject7/tools/check_docs.py . && .venv/bin/python scripts/qa_acceptance_check.py
```

## 5. 판정 기준 (모두 같은 Val 104장)

- 비교 대상(exp007 = 0.724)보다 **mAP50-95 +0.02 이상**이면 채택, 그 밖은 보류·기각. exp013 결과로 흔들림 폭이 0.02 보다 크면 기준을 다시 정한다.
- 타일링(exp010)은 학습 중 Val 이 조각 단위라 `tiling_eval_exp010.csv` (원본 단위, 같은 코드로 잰 exp007 과 비교) 로 판정한다.
- 점수만이 아니라 **학습 시간 · 예측 속도 · Class 별(특히 갈변·벌레)** 도 함께 적는다.

## 6. 알아 둘 것

- GPU 메모리 측정 (RTX 3060 12GB): 11n·2560·batch 3 = 10.8GB · 11s·1920·batch 3 = 9.0GB · 11s·2560 은 batch 2 도 13.6GB (불가). 2560 은 학습 5시간 → 이번 계획에서 뺐다.
- 학습이 끝났는데 조건 기록에서 오류가 나면 학습을 다시 하지 말고 `python scripts/11_train_v5.py --run <실험> --report-only`.
- 실행 폴더·Weight 가 이미 있으면 스크립트가 멈춘다 (덮어쓰지 않음). 실패한 실행을 다시 하려면 `runs/<실행>/` 만 지운다 (`results.csv` 가 없을 때만).
- 갈변(작은 점)은 Train 에 4개뿐이라 이번 실험들로도 크게 좋아지기 어렵다 — 한계로 기록돼 있다 ([`baseline_vs_improved.md`](../../reports/04_improvement/baseline_vs_improved.md) 3장).
