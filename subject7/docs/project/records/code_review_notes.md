# 코드 문서화 중 남긴 확인 항목

[← 프로젝트 문서](../README.md)

이전 코드 문서화에서 남긴 확인 항목입니다. 이번 문서 정리는 이 항목들의 재현·수정을 수행하지 않았으며, 현재 버그로 확정하는 목록은 아닙니다. 각 코드 설명서와 실제 구현을 대조해 확인합니다.

| 위치 | 내용 |
|---|---|
| [`main_window`](../../src/ui/main_window.md) | 검수 기록 칸만 고친 뒤 Undo/Redo 로 BBox 를 처음 상태로 돌리면 `dirty` 가 꺼져, 다음 사진으로 넘어갈 때 입력칸 변경이 묻지 않고 버려질 수 있다 |
| [`yolo_loader`](../../src/yolo/yolo_loader.md) ↔ [`validator`](../../src/validation/validator.md) | Class `2.0` 을 화면은 Class 2 로 읽고, Validation·`import_labels` 는 `BAD_NUMBER` 로 본다 |
| [`build_final`](../../tools/build_final.md) | `제외` 사진이 한 장이라도 있으면 최종본을 만들지 않는다 (건너뛰는 것이 아님) |
| [`import_labels`](../../tools/import_labels.md) | 덮어쓰기 백업이 원래 폴더 구조가 아니라 파일 이름만으로 저장된다 (docstring 과 다름) |
| [`share_server`](../../tools/share_server.md) | 기본 검수 범위에 501~550번이 빠져 있다. PM 가이드가 안내하는 `공유시작.bat` 은 저장소에 없다 |
| [`qa_summary`](../../tools/qa_summary.md) | 사람 이름·Human QA 결과·일부 수치 문장이 코드에 고정되어 있다 |
| [`yolo_writer`](../../src/yolo/yolo_writer.md) | TXT 를 원자적으로 저장하지 않는다 (검수표·세션은 원자적 저장) |
