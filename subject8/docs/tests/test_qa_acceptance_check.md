# `tests/test_qa_acceptance_check.py`

> 인수 점검이 현행 GUI·발표 경로를 인식하고, 미제공·미검증을 PASS로 바꾸지 않는지 검사합니다.

[코드 보기](../../tests/test_qa_acceptance_check.py) · [문서 목차](../README.md)

`subject8/`에서 실행합니다. 표준 라이브러리만 쓰며, 실제 사진·영상·모델은 열지 않습니다.

```bash
python -m unittest discover -s tests -p 'test_qa_acceptance_check.py' -v
```

- GUI 후보 TXT 구현은 전용 배치 스크립트 없이도 별도로 확인합니다.
- GUI가 없는데 배치 파일만 있다고 후보 저장을 PASS로 보지 않습니다.
- 현행 `presentation/private/videos/`를 검사하고, 비어 있는 구형 `demo/`는 참고로 표시합니다.
- 0바이트 영상은 준비된 파일로 세지 않습니다. 실제 재생 품질은 이 테스트가 보장하지 않습니다.
- `--output`은 기존 결과를 보존하며, 같은 프로세스에서 반복 실행해도 결과 행이 누적되지 않습니다.
