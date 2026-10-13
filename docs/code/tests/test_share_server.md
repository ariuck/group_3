# `tests/test_share_server.py`

> 결과 주고받기 서버 시험. 이 PC 안(`127.0.0.1`)에서 가짜 zip 으로 실제 HTTP 요청을 보내 확인한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../tests/test_share_server.py) · 대상: [`tools/share_server`](../tools/share_server.md)

## 실행

```bash
python -m unittest tests/test_share_server.py
```

## 시험 내용 (`ShareServerTest`)

| 묶음 | 확인하는 것 |
|---|---|
| 접근 | 페이지는 번호 없이 보이지만 데이터는 번호 필요 · 여러 번 틀리면 잠김 · 없는 주소 404 · 올리기도 번호 필요 |
| 내려받기 | `보내기/` 폴더의 파일만 목록·내려받기 |
| 올리기 | 올바른 zip 은 저장 + 풀림 · 같은 이름은 덮어쓰지 않음 · 위험하거나 잘못된 파일 거부 · 이름은 zip 이어야 하고 폴더 부분 제거 · 너무 큰 파일 거부 · 풀면 너무 커지는 zip 거부 |
| 페이지 | 단계별 가이드와 검수 범위 · 끌어다 놓기·내려받기 버튼·번호 칸 · 표시되는 최대 크기가 설정을 따름 · 사용자 지정 범위 표시 |
| 도우미 | `parse_assign` · 기타 함수 |
