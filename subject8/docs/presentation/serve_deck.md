# `subject8/presentation/serve_deck.py`

> **발표 서버** — 교과 7·8 통합 발표자료(`index.html` · `발표대본.html` · `assets/` · `private/` 사진·영상)를 이 PC 의 LAN 에 8765 포트로 연다. `/demo/` 요청은 이 PC 의 시연 프로그램(`app/server.py`, 8010)으로 전달한다. 표준 라이브러리만 쓴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../presentation/serve_deck.py) · [발표자료 안내](../../presentation/README.md)

## 사용법

보통은 `발표서버 시작.bat` → `start_presentation.ps1` 이 Windows Python 으로 이 파일을 실행하고, WSL 의 시연 프로그램(`subject8/.venv/bin/python app/server.py`)도 함께 켠다.

```bash
cd subject8
python3 presentation/serve_deck.py                  # http://127.0.0.1:8765/index.html#1
python3 presentation/serve_deck.py --port 8766      # 8765 를 다른 프로그램이 쓰고 있을 때
python3 presentation/serve_deck.py --demo-port 8010 # 시연 프로그램 포트
```

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `ROOT` | 이 파일이 있는 폴더 (`subject8/presentation/`) — 이 밖의 파일은 열지 않는다 |
| `Handler._serve()` | `index.html` · `발표대본.html` · `assets/` · `private/` 만 열고 나머지는 404. 폴더 목록은 보여 주지 않음 |
| `Handler._proxy()` | `/demo/…` 를 `127.0.0.1:<demo-port>` 로 전달 (주소 고정, 41MB 넘는 요청 거절). 시연 프로그램이 꺼져 있으면 503 |
| `Handler.end_headers()` | 모든 응답에 `Cache-Control: no-store` (고친 화면이 바로 보이게) |
| `lan_ips()` | 팀원에게 알려 줄 이 PC 의 LAN 주소 |
| `main()` | `--port`(기본 8765) · `--demo-port`(기본 8010) 로 서버 실행 |

## 의존성

- **사용하는 것**: 표준 라이브러리 (`http.server`, `http.client`, `socket`, `pathlib`)
- **사용하는 곳**: `presentation/start_presentation.ps1`, 발표 화면의 시연 연결 `presentation/assets/demo-bridge.js` (`/demo/`)

## 주의사항

- `0.0.0.0` 에 열리므로 같은 네트워크에서는 `private/` 의 사진·영상도 볼 수 있다. 발표 때만 켜고 끝나면 창을 닫는다.
- 사진·영상은 Git 에 없다. 각 PC 의 `private/photos/` · `private/videos/` 에 넣어야 화면이 다 보인다.
