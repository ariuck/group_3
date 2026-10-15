# group_3 — AI Campus 조각김치 이물검출

| 폴더 | 내용 | 시작하기 |
|---|---|---|
| [`subject7/`](subject7/README.md) | 교과 7 — YOLO 라벨링 프로그램 (BBox·Class 검수, FINAL 데이터 생성) | `cd subject7 && python main.py` |
| [`subject8/`](subject8/README.md) | 교과 8 — YOLO11n 객체검출 (Baseline · 실패분석 · 개선 실험) | [README](subject8/README.md) 참고 |

```text
group_3/
├── subject7/                      교과 7 라벨링 프로그램 (src, tests, tools, docs, data …)
├── subject8/                      교과 8 객체검출 (src, scripts, reports, models …)
├── .venv/                         공용 가상환경 (Git 제외)
├── .gitignore                     저장소 공통 규칙 (폴더별 규칙은 각 폴더의 .gitignore)
└── .mailmap
```

- 두 프로젝트는 서로의 폴더 이름을 기준으로 경로를 만든다. 교과 8 의 `04_import_label_fixes.py` 는 `subject7/data/work/_RAW밖/` 에서 수정한 라벨을 가져온다.
- **NDA**: 회사 제공 사진·라벨·검수표는 Git 에 올리지 않는다 (`subject7/.gitignore`, `*.jpg` 공통 규칙).
