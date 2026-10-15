# `tests/day1_selftest.py`

> 1일차 자체 점검. 임시 폴더에 가짜 데이터를 만들어 RAW/WORK 분리 · 데이터 조사 · End-to-End · RAW 불변 · Class 설정 · Zoom·편집을 실제 화면 객체로 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/day1_selftest.py)

## 실행

```bash
python tests/day1_selftest.py        # 화면(Tk) 필요. 항목마다 OK / FAIL 출력
```

`data/raw` 의 실제 데이터는 읽지도 건드리지도 않는다.

## 점검 항목

| 묶음 | 내용 |
|---|---|
| Class 설정 | 7개(0~6) 읽기, 이름이 기준 문서와 같음, Class 4 사용 안 함, 설정 파일이 없으면 기본값 |
| 순수 함수 | 좌표 왕복, BBox 잘라내기·정렬, 너무 작은 영역 거부, 겹치면 작은 BBox 선택 |
| 데이터 조사 | 데이터셋/split 별 이미지·TXT·짝·빈 TXT, Class 4 BBox 발견, Markdown 표 |
| 경로 | 출처 판별, WORK 가 RAW 와 같은 구조, 같은 이름 TXT 자동 탐색 |
| End-to-End | TXT 자동 Load → 드래그로 추가 → 2px 실수 드래그 무시 → 저장 → 검수표 생성(19칸, 자동 칸, 상태 수정 완료, 검수일) → 다시 불러오기 복원 → 같은 사진은 줄 갱신 → 사람 칸·`수정 필요` 보존 |
| RAW 보호 | RAW TXT 해시 불변, RAW 안 저장 거부 |
| Zoom·편집 | 화면 맞춤, 휠 확대(커서 지점 고정)·축소, 확대 상태에서 그린 BBox 도 원본 좌표, Undo/Redo, 오른쪽 드래그 이동, 2000% 에서도 그리기, 배율과 무관한 저장 좌표 |
| 특수 상황 | 빈 TXT, TXT 없음, 고치지 않고 저장하면 `검수 전`, 머리글이 다른 검수표는 덮어쓰지 않음, RAW 밖 이미지는 기록 안 함 |

## 대상 코드

[`settings`](../src/settings.md) · [`bbox_manager`](../src/bbox/bbox_manager.md) · [`data_paths`](../src/data_paths.md) · [`manifest_writer`](../src/manifest/manifest_writer.md) · [`main_window`](../src/ui/main_window.md) · [`validator`](../src/validation/validator.md) · [`coords`](../src/yolo/coords.md) · [`yolo_loader`](../src/yolo/yolo_loader.md)
