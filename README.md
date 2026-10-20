# group_3 — AI Campus 조각김치 이물검출

| 폴더 | 내용 | 시작하기 |
|---|---|---|
| [`subject7/`](subject7/README.md) | 교과 7 — YOLO 라벨링 프로그램 (BBox·Class 검수, FINAL 데이터 생성) | `cd subject7 && python main.py` |
| [`subject8/`](subject8/README.md) | 교과 8 — YOLO11n 객체검출 (Baseline · 실패분석 · 개선 실험) | [README](subject8/README.md) 참고 |
| [`presentation/`](presentation/README.md) | 교과 7 + 8 공동 발표자료 (HTML 한 파일, 인터넷 없이 열림) | `presentation/index.html` 을 브라우저로 열기 |

```text
group_3/
├── subject7/                      교과 7 라벨링 프로그램 (src, tests, tools, docs, data …)
├── subject8/                      교과 8 객체검출 (src, scripts, reports, models …)
├── presentation/                  발표자료 (교과 7 + 8) — index.html · assets · backup (사진 private/ 은 Git 제외)
├── .venv/                         공용 가상환경 (Git 제외)
├── .gitignore                     저장소 공통 규칙 (폴더별 규칙은 각 폴더의 .gitignore)
└── .mailmap
```

- 두 프로젝트는 서로의 폴더 이름을 기준으로 경로를 만든다. 교과 8 의 `04_import_label_fixes.py` 는 `subject7/data/work/_RAW밖/` 에서 수정한 라벨을 가져온다.
- **NDA**: 회사 제공 사진·라벨·검수표는 Git 에 올리지 않는다 (`subject7/.gitignore`, `*.jpg` 공통 규칙).

## 폴더 구조 변경 후 처음 받을 때 (2026-10-15, `subject7/` · `subject8/` 분리)

Git 이 관리하지 않는 데이터(사진·작업 라벨·검수표 CSV·`.venv` 등)는 `git pull` 로 따라오지 않고 옛 위치(`data/`, `manifests/`, `reports/`, `subject8_kimchi_detection/`)에 남는다. **그 상태에서 VS Code 의 "모두 스테이징(+)" 을 누르면 회사 데이터가 커밋된다.** 받은 직후 아래 순서로 옮긴다 (WSL).

1. 라벨링 프로그램을 끄고 받는다: `cd ~/group_3 && git pull origin main`
2. 데이터를 새 폴더로 옮긴다 (이동, 이미 있는 파일은 덮어쓰지 않음):

   ```bash
   cd ~/group_3 && for p in data:subject7/data manifests:subject7/manifests reports:subject7/reports subject8_kimchi_detection:subject8; do rsync -a --remove-source-files --ignore-existing "${p%%:*}/" "${p##*:}/" 2>/dev/null; done; find data manifests reports subject8_kimchi_detection src tests tools -type d -empty -delete 2>/dev/null; echo 끝
   ```

3. 교과 8 가상환경 경로를 고친다 (교과 8 을 쓰는 사람만, `ok` 가 나오면 끝):

   ```bash
   cd ~/group_3/subject8 && grep -rIl subject8_kimchi_detection/.venv .venv/bin .venv/pyvenv.cfg | xargs -r sed -i 's#subject8_kimchi_detection/.venv#subject8/.venv#g' && .venv/bin/python -c "import ultralytics; print('ok')"
   ```

4. 확인: `git status --short` 에 아무것도 없고, 맨 위에 `subject7`·`subject8`·`README.md` 만 보이면 끝. 옛 폴더가 남아 있으면 지우지 말고 팀에 알린다.
5. 실행 위치: 교과 7 은 `cd ~/group_3/subject7 && ~/group_3/.venv/bin/python main.py`, 교과 8 은 VS Code 로 `subject8` 폴더를 연다.
