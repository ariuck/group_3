# 실험 인수인계 · 3대 분산 학습 계획 (kimchi_v5)

> 작성 2026-10-19 · 정리 담당 ariuck (`feature/ariuck`). 이 문서만 보고 다른 PC 에서 이어서 실험할 수 있게 쓴다.

## 1. 지금까지 (요약)

- **공식 Dataset `kimchi_v5`** — v4 Val 의 누수(132장 중 83장이 Train 과 같은 촬영 묶음)를 없앤 재분할. Train 558 / Val 104 / Test 82 / Bridge 156. 기준 [`kimchi_v5_split.md`](kimchi_v5_split.md)
- **실험 8개** (같은 Val 104장, mAP50-95): baseline 0.470 → 1280 0.646 → 1920 0.704 → **11s·1920·증강(exp007) 0.724 (현재 최고)**. 전체 표·개선점·한계: [`reports/04_improvement/baseline_vs_improved.md`](../../reports/04_improvement/baseline_vs_improved.md), 판정 [`experiment_log.csv`](../../reports/04_improvement/experiment_log.csv), 모델 목록 [`models/README.md`](../../models/README.md)
- **Final Model 은 아직 정하지 않았다.** 아래 분산 실험 결과를 보고 8일차에 Val 근거로 정한다.
- **Frozen Test(G07·G14)·Bridge Holdout 은 쓰지 않는다.** 예측 스크립트도 막혀 있다.

## 2. 3대 분산 계획

세 PC 모두 학원 컴퓨터로 사양이 같다 (RTX 3060 12GB). 모든 실험은 **exp007 (YOLO11s · imgsz 1920 · batch 3 · 증강 flipud 0.5·hsv_v 0.6 · 50 epoch)** 에서 한 변수씩 바꾼다. 조건은 `scripts/11_train_v5.py` 의 `RUNS` · `scripts/14_train_tiles_v5.py` 의 `TILE_EXPS` 에 **이미 다 등록**돼 있어서, 각자 명령만 실행한다 (코드를 고치지 않으므로 브랜치끼리 충돌하지 않음).

| 담당 · 브랜치 | 실험 | 바꾸는 것 (exp007 대비) | 알고 싶은 것 | 예상 시간 |
|---|---|---|---|---|
| **상우** · `feature/sonny` | exp008 | epochs 50 → 100 | exp007 이 50 epoch 에서 아직 오르는 중 → 더 오르나 | 약 1시간 30분 |
| | exp013 | seed 42 → 7 | 같은 조건 반복 시 점수가 얼마나 흔들리나 (0.02 차이가 의미 있나) | 약 45분 |
| | exp012 | imgsz 1920 → 1280 (batch 6) | 더 가볍고 빠른 후보 (교과 14 현장용) | 약 25분 |
| **동연** · `feature/ariuck` (정리 담당 겸) | exp010 | 입력: 원본 → 2×2 타일링 | 큰 모델 + 타일링이 작은 이물(갈변·가지)에 더 효과적인가 | 약 3시간 |
| **혜성** · `feat/hyesung` | exp009 | YOLO11s → **11m** (batch 2) | 모델을 더 키우면 더 오르나 | 약 2시간 30분~3시간 |
| | exp011 | 증강 끄기 | 11s 에서 증강이 실제로 도움이 되나 (효과 분리) | 약 45분 |

- 11m 메모리 측정 (2026-10-19, 이 사양): imgsz 1920 · batch 2 = **9.8GB** (12GB 안). 넘치면(속도가 갑자기 몇 배 느려짐 · `out of memory`) 멈추고 알려 준다 — batch 1 로 낮추지 않는다 (BatchNorm 이 불안정해짐).
- 한 PC 에서는 **한 번에 하나만** 학습한다 (같이 돌리면 메모리가 넘쳐 꺼진 적 있음). 아래 명령은 `&&` 로 차례로 이어서 돌린다.

## 3. 각 PC 에서 실행하는 법

### 처음 한 번 (세 PC 공통)

```bash
# 1) 저장소 받기 (이미 있으면 cd ~/group_3 && git fetch origin)
git clone https://github.com/ariuck/group_3.git ~/group_3

# 2) 회사 원본 폴더 2개를 그대로 subject7/data/raw/ 에 복사 (USB — 외부 클라우드·메신저 금지)
#    subject7/data/raw/이물검출_학습데이터1/…  subject7/data/raw/이물검출_학습데이터2/…
```

### 상우 — `feature/sonny`

```bash
cd ~/group_3 && git fetch origin && git checkout feature/sonny && git pull
cd subject8 && python3 scripts/00_setup.py                 # 마지막에 "같은 데이터 · 같은 분할 ✓"
.venv/bin/python scripts/11_train_v5.py --run exp008 && \
.venv/bin/python scripts/11_train_v5.py --run exp013 && \
.venv/bin/python scripts/11_train_v5.py --run exp012       # 약 2시간 40분
```

### 동연 — `feature/ariuck`

```bash
cd ~/group_3 && git fetch origin && git checkout feature/ariuck && git pull
cd subject8 && python3 scripts/00_setup.py
.venv/bin/python scripts/14_train_tiles_v5.py --exp exp010  # 조각 만들기 → 학습 → 원본 Val 채점, 약 3시간
```

### 혜성 — `feat/hyesung`

```bash
cd ~/group_3 && git fetch origin && git checkout feat/hyesung && git merge origin/main   # 최신 main 반영
cd subject8 && python3 scripts/00_setup.py
.venv/bin/python scripts/11_train_v5.py --run exp009 && \
.venv/bin/python scripts/11_train_v5.py --run exp011       # 약 3시간 30분
```

- 학습 화면을 닫아도 계속 돌게 하려면 `nohup <명령> > train.log 2>&1 &` 로 실행하고 `tail -f train.log` 로 본다.
- 각 실험이 끝나면 화면 마지막에 `PASS … Weight 별도 보관` 과 `(참고) best epoch N: mAP50 … / mAP50-95 …` 가 나온다. 이 숫자를 커밋 메시지에 적는다.

## 4. 브랜치에 무엇이 올라가나

**모델도 올라간다** (`models/improved/<실행>.pt` — 11s 약 19MB, 11m 약 40MB). 김치 사진만 빼고 결과를 다 올려서 다른 PC 에서 바로 평가·예측·그래프를 볼 수 있게 한다.

| 올린다 (자기 실험 이름이 들어간 것만) | 내용 | 크기 |
|---|---|---|
| `runs/<실행>/results.csv` · `args.yaml` | epoch 별 학습 기록 · 실제로 쓴 설정 | 작음 |
| `runs/<실행>/*.png` · `labels.jpg` | Confusion Matrix · PR 곡선 · 학습 곡선 · 박스 분포 그림 (사진 아님) | 약 1.6MB |
| `models/improved/<실행>.pt` | 학습된 모델 (best epoch) | 19~40MB |
| `reports/04_improvement/<실행>_training_condition.md` | 학습 조건 · GPU · 시간 · 점검 결과 | 작음 |
| (동연) `reports/04_improvement/tiling_eval_exp010.csv` | 타일링 원본 단위 채점 | 작음 |

| 올리지 않는다 | 이유 |
|---|---|
| 김치 사진 · `runs/<실행>/*_batch*.jpg` · `runs/<실행>/weights/` · `data/` | 회사 사진 (`.gitignore` 가 자동으로 막음) · `weights/` 는 `models/` 와 중복 |
| `models/README.md` · `reports/runs_summary.csv` · `reports/figures/` · `experiment_log.csv` | 여러 사람이 같이 고치면 충돌 → 정리 담당(동연)이 합친 뒤 한 번에 만든다 |
| `scripts/` · `src/` · `docs/` | 고칠 일이 생기면 따로 알려 준다 |

```bash
# 상우 예 (실험마다 한 번씩, 또는 셋을 한꺼번에) — 실행 이름은 학습 화면·runs/ 폴더 이름 그대로
cd ~/group_3
R=exp008_v5_s_imgsz1920_aug_epoch100
git add subject8/runs/$R subject8/models/improved/$R.pt subject8/reports/04_improvement/${R}_training_condition.md
git status                                  # 초록색이 위 파일들뿐인지 확인 (사진·weights 가 없어야 함)
git commit -m "feat(subject8): $R — Val mAP50-95 0.xxx · 학습 N분"
git push origin feature/sonny               # 혜성: feat/hyesung · 동연: feature/ariuck
```

| 담당 | 실행 이름 (`R=`) |
|---|---|
| 상우 | `exp008_v5_s_imgsz1920_aug_epoch100` · `exp013_v5_s_imgsz1920_aug_seed7` · `exp012_v5_s_imgsz1280_aug` |
| 동연 | `exp010_v5_s_tile2x2_aug` (+ `tiling_eval_exp010.csv`) |
| 혜성 | `exp009_v5_m_imgsz1920_aug` · `exp011_v5_s_imgsz1920` |

푸시한 뒤 정리 담당(동연)에게 알려 준다. 특이사항(메모리 넘침, 중간에 꺼짐 등)도 같이.

## 5. 정리 담당이 합칠 때 (동연 · `feature/ariuck`)

```bash
cd ~/group_3 && git checkout feature/ariuck && git fetch origin
git merge origin/feature/sonny origin/feat/hyesung          # 실행 이름이 달라 충돌 없음
cd subject8 && .venv/bin/python scripts/plot_runs.py          # 그래프 · runs_summary · models/README
# experiment_log.csv 에 실험별 한 줄 + 판정, baseline_vs_improved.md 표·개선점 갱신
.venv/bin/python ../subject7/tools/check_docs.py . && .venv/bin/python scripts/qa_acceptance_check.py
cd .. && git add -A subject8 && git commit -m "…" && git fetch . feature/ariuck:main && git push origin main feature/ariuck
```

## 6. 판정 기준 (모두 같은 Val 104장)


- 비교 대상(exp007 = 0.724)보다 **mAP50-95 +0.02 이상**이면 채택, 그 밖은 보류·기각. exp013 결과로 흔들림 폭이 0.02 보다 크면 기준을 다시 정한다.
- 타일링(exp010)은 학습 중 Val 이 조각 단위라 `tiling_eval_exp010.csv` (원본 단위, 같은 코드로 잰 exp007 과 비교) 로 판정한다.
- 점수만이 아니라 **학습 시간 · 예측 속도 · Class 별(특히 갈변·벌레)** 도 함께 적는다.

## 7. 알아 둘 것

- GPU 메모리 측정 (RTX 3060 12GB): 11n·2560·batch 3 = 10.8GB · 11s·1920·batch 3 = 9.0GB · 11s·2560 은 batch 2 도 13.6GB (불가). 2560 은 학습 5시간 → 이번 계획에서 뺐다. 11m·1920·batch 2 = 9.8GB.
- 학습이 끝났는데 조건 기록에서 오류가 나면 학습을 다시 하지 말고 `python scripts/11_train_v5.py --run <실험> --report-only`.
- 실행 폴더·Weight 가 이미 있으면 스크립트가 멈춘다 (덮어쓰지 않음). 실패한 실행을 다시 하려면 `runs/<실행>/` 만 지운다 (`results.csv` 가 없을 때만).
- 갈변(작은 점)은 Train 에 4개뿐이라 이번 실험들로도 크게 좋아지기 어렵다 — 한계로 기록돼 있다 ([`baseline_vs_improved.md`](../../reports/04_improvement/baseline_vs_improved.md) 3장).
