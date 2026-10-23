# 문서 작성·공유 규칙

[← 전체 프로젝트](README.md) · [교과 7 문서](subject7/docs/README.md) · [교과 8 문서](subject8/docs/README.md)

## 문서의 역할

| 위치 | 담는 내용 |
|---|---|
| 루트 `README.md` | 프로젝트 소개·핵심 결과·구성·첫 방문자의 읽는 순서 |
| `subject7/README.md` · `subject8/README.md` | 해당 교과의 역할·빠른 시작·결과 요약·문서 링크 |
| 각 교과의 `docs/README.md` | 코드 설명서와 프로젝트 문서의 목차 |
| 각 교과의 `docs/<원본 경로>.md` | 원본 파일의 역할·입출력·주요 구성요소·사용법·주의사항 |
| 각 교과의 `docs/project/` | 상세 가이드·기준서·설계·팀 운영·과정 기록·시연·인계 |
| 각 교과의 `reports/` | 검증·실험의 결과와 근거 파일 |
| `subject8/presentation/` | 교과 7·8 통합 발표 화면·대본·진행표 (2026-10-22 발표본) |

## 코드 경로를 그대로 미러링

기준은 **저장소 전체가 아니라 각 교과 폴더의 루트**입니다. `docs/code/`라는 중간 폴더를 만들지 않습니다.

```text
subject7/main.py                      → subject7/docs/main.md
subject7/src/ui/main_window.py        → subject7/docs/src/ui/main_window.md
subject7/tests/test_bbox_edit.py      → subject7/docs/tests/test_bbox_edit.md
subject8/scripts/00_setup.py          → subject8/docs/scripts/00_setup.md
subject8/app/server.py                → subject8/docs/app/server.md
subject8/presentation/serve_deck.py   → subject8/docs/presentation/serve_deck.md
subject8/manifests/…/tools/groups.py   → subject8/docs/manifests/…/tools/groups.md
```

- Python 파일을 추가·이름 변경·삭제하면 **같은 커밋에서** 대응 문서도 함께 바꿉니다. 비어 있는 `__init__.py`는 제외합니다.
- 자동 대응 검사는 Python 파일을 대상으로 합니다. 설정·HTML·CSS·JS의 별도 설명서까지 모두 검사하는 것은 아닙니다. 현재 웹 화면 구성은 서버 설명서의 의존 관계에서 안내합니다.
- 코드 설명서는 **한 줄 요약 → 역할·입출력 → 주요 구성요소 → 의존 관계 → 사용 예 → 주의사항** 순서로 씁니다. 테스트 문서는 실행 방법과 확인 항목을 중심으로 짧게 씁니다.
- 코드 설명서에서 기준·정책의 본문을 중복 작성하지 말고 `docs/project/`의 기준 문서로 연결합니다.

## `docs/project/` 안에서 정리하기

- `guides/`: 설치·사용·실험 등 여러 코드 파일에 걸친 작업 안내
- `standards/` · `design/` · `team/`: 기준서·설계·팀 운영 (해당 문서가 있는 교과만)
- `process/` · `records/` · `meetings/`: 과정·작업 기록·회의록
- `handoff/`: 다음 교과로 넘기는 결과·제약·재현 절차
- `images/`: 공개 가능한 설명 그림·가상 샘플 화면

일반 프로젝트 문서는 `docs/` 바로 아래에 흩어 놓지 않습니다. 새 분류는 실제 문서가 필요할 때 만들고, `기타/` 하나에 계속 쌓아 두지 않습니다.

## 결과와 상태를 쓰는 기준

교과 7·8의 종료 상태는 [PROJECT_STATUS.md](PROJECT_STATUS.md)를 기준으로 봅니다. 과거 계획의 `예정`·`TODO`를 현재 진행 중인 작업으로 옮겨 쓰지 않습니다. 미제공 기능과 시험 기록이 없는 항목도 완료로 바꾸지 않고 따로 기록합니다. 후속 교과의 대상·모델·방향은 확정된 사실만 적습니다.

- 성능에는 **Dataset Version·split·지표·평가 조건**을 함께 적습니다. 서로 다른 버전이나 Val/Test를 같은 비교로 묶지 않습니다.
- 핵심 결과의 근거는 `reports/`의 CSV·보고서에 두고 README에는 필요한 요약과 링크만 둡니다.
- `models/README.md`처럼 스크립트가 만드는 문서는 생성 원본을 고쳐 다시 생성합니다.
- 설계 초안·과거 버전·미완성 기능은 현행 결과와 구분합니다. 후보 TXT 저장과 전체 Auto Label 작업의 완료를 같은 것으로 표현하지 않습니다.
- 명령어는 어느 폴더에서 실행하는지 적습니다. 공통 README에는 개인 PC의 절대 경로를 기본 실행법으로 넣지 않습니다.

## 교과별 가상환경과 의존성

각 교과는 자기 폴더 안에 `requirements.txt`와 가상환경 `.venv`를 둡니다. 저장소 맨 위에 공용 `.venv`를 만들지 않습니다.

| 교과 | 가상환경 | 의존성 | 준비 |
|---|---|---|---|
| 교과 7 | `subject7/.venv` | `subject7/requirements.txt` | [교과 7 README](subject7/README.md) (교과 8 올인원 준비가 함께 만듦) |
| 교과 8 | `subject8/.venv` | `subject8/requirements.txt` | `cd subject8 && python3 scripts/00_setup.py` |

- 교과 7·8은 하나로 이어진 프로젝트입니다. 교과 8이 `subject7/data/`의 최종 라벨·원본 사진을 직접 읽고, [`00_setup.py`](subject8/docs/scripts/00_setup.md)는 이 두 교과의 가상환경·데이터만 준비합니다.
- 새 교과(예: `subject9/`)는 교과 7·8과 독립입니다. 자기 폴더 안에 `requirements.txt`·`.venv`·준비 방법(README)을 두고, `subject7/`·`subject8/`의 가상환경이나 `00_setup.py`에 기대지 않습니다. `00_setup.py`에 다른 교과의 단계를 넣지 않습니다.
- 다른 교과의 결과(라벨·모델 등)를 가져다 쓰면 어느 파일을 어떤 버전으로 쓰는지 그 교과의 README에 적습니다.
- `.venv/`는 저장소 맨 위 `.gitignore`가 어느 폴더에서든 제외합니다.

## 커밋 전 확인

저장소 루트에서 실행합니다. 문서의 존재 여부를 검사하며, 내용·화면·성능까지 검증하는 명령은 아닙니다.

```bash
python3 subject7/tools/check_docs.py subject7
python3 subject7/tools/check_docs.py subject8
git diff --check
git status --short
```

이동한 문서의 상대 링크·그림·앵커와 관련 코드의 경로 참조도 함께 확인합니다. Markdown 링크는 GitHub에서 열 수 있는 저장소 상대 경로를 씁니다.

원본 사진·RAW·WORK·작업 중 검수표·실제 사진이 포함된 캡처와 영상은 공개 Git에 올리지 않습니다. 최종 라벨·허용된 검수표·모델·학습 기록·그래프만 `.gitignore`에 따라 공유합니다. 파일을 지정해 스테이징하고 커밋 대상에 원본 사진이 없는지 확인합니다.
