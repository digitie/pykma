# 기여 가이드

`pykma` 개선에 참여할 때 참고하는 문서입니다. 이 프로젝트는 까다로운 공공 API를 감싸므로, 좋은 변경은 작고 테스트가 있으며 KMA 특유의 예외 상황을 명시적으로 다룹니다.

## 로컬 준비

```bash
python -m venv .venv
pip install -e ".[dev]"
python -m pytest
```

기본 테스트는 실제 KMA API를 호출하면 안 됩니다.

## 코드 변경 전 읽을 문서

1. `AGENTS.md`: 작업 소유권과 검증 기준.
2. `kma-api.md`: endpoint 동작과 KMA 응답의 함정.
3. `docs/repeated-mistakes.md`: 이미 겪었거나 반복되기 쉬운 실수.
4. `SKILL.md`: 구현 불변조건.
5. `docs/apihub.md`: APIHub 함수형 래퍼와 응답 형식.

## 코드 규칙

- 의도적이고 문서화된 변경이 아니라면 public API를 안정적으로 유지합니다.
- timezone 없는 `datetime`은 KST로 해석합니다.
- `requests`의 `params=`에는 data.go.kr Decoding 인증키를 전달합니다.
- 예보 항목의 `PCP`, `SNO` 범주 문자열은 보존합니다.
- `PTY` 매핑은 endpoint별로 다르게 처리합니다.
- KMA `resultCode`가 `00`이 아니면 typed exception으로 변환합니다.
- APIHub의 이름 없는 query string은 순서를 보존합니다.
- 동작 변경에는 테스트를 함께 추가합니다.

## 테스트

기본 검증:

```bash
python -m pytest
python -m compileall pykma tests
```

선택 검증:

```bash
ruff check .
mypy pykma
```

실제 API 호출 테스트는 반드시 opt-in이어야 합니다.

```bash
KMA_SERVICE_KEY=<decoded key> python -m pytest -m integration
```

실제 인증키, 인증키가 포함된 URL, 비밀값이 들어 있는 응답 fixture는 커밋하지 않습니다.

## 문서화

사용자에게 보이는 동작이 바뀌면 다음 중 하나 이상을 갱신합니다.

- `README.md`: 사용법과 예제.
- `kma-api.md`: API 세부 사항.
- `docs/troubleshooting.md`: 증상과 해결책.
- `docs/repeated-mistakes.md`: 반복 실수를 막는 규칙.
- `docs/api-coverage.md`: 구현 범위와 API 개수.
- `docs/apihub-endpoints.md`: APIHub 함수형 endpoint 목록.
- `CHANGELOG.md`: 릴리스 관점의 변경 사항.

APIHub 공식 목록을 갱신할 때는 다음을 실행해 코드와 문서를 함께 생성합니다.

```bash
python -X utf8 tools/update_apihub_endpoints.py
```

## 커밋 메시지

짧은 명령형 문장을 사용합니다. 커밋 메시지는 필요하면 영어를 사용할 수 있지만, 프로젝트 문서는 한글로 작성합니다.

```text
Add endpoint-aware precipitation labels
```

서로 관련 없는 리팩터링은 기능/버그 수정 커밋에 섞지 않습니다.
