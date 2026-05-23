# Architecture Decision Records

결정을 뒤집으면 기존 ADR을 삭제하지 않고 `[SUPERSEDED by ADR-NNN]`으로 표시한다.

## ADR-001: httpx 기반 HTTP 클라이언트

- **상태**: 확정
- **결정**: `requests` 대신 `httpx`를 사용한다.
- **이유**: sync/async 통합 API, `follow_redirects` 기본 지원, `params=` 인코딩 동작이 data.go.kr serviceKey 전달에 적합.
- **결과**: `_http.py`에서 `httpx.Client`/`httpx.AsyncClient`를 생성하고, `get_with_retries`/`async_get_with_retries`로 재시도를 처리한다.

## ADR-002: Pydantic v2 frozen 모델

- **상태**: 확정
- **결정**: 모든 public 응답 모델은 `pydantic.BaseModel`에 `ConfigDict(frozen=True, extra="forbid")`를 적용한다.
- **이유**: 불변 모델은 캐시 키 생성, 비교, 직렬화에서 예측 가능한 동작을 보장. `extra="forbid"`는 API 응답 변경 시 조기 감지.
- **결과**: `kmaModel` 기본 클래스를 `models.py`에 정의하고 모든 public 모델이 상속.

## ADR-003: 인증값 보안 정책

- **상태**: 확정
- **결정**: `serviceKey`, `authKey` 등 인증값은 로그, fixture, 모델 repr, 캐시 키에 포함하지 않는다.
- **이유**: 키 유출 방지. `ResponseMetadata.request_params`에서 자동 삭제.
- **결과**: `metadata.py`의 `sanitize_request_params()`, `redact_credentials_in_text()`, `redact_url_credentials()`로 전방위 보호.

## ADR-004: data.go.kr/APIHub 이중 gateway 분리

- **상태**: 확정
- **결정**: `DataGoKrClient`(serviceKey)와 `ApiHubClient`(authKey)를 별도 클라이언트로 유지한다. 통합 facade를 만들지 않는다.
- **이유**: 인증 방식, 응답 형식, 승인 상태가 다르므로 혼용 시 디버깅이 어렵다. 109개 정확 중복 operation은 문서로 관리.
- **결과**: `docs/datagokr-apihub-overlap.md`에 중복 현황 문서화. 카탈로그에 `gateway` 필드로 명시.

## ADR-005: 파싱 도우미 공유 모듈

- **상태**: 확정 (2026-05-23)
- **결정**: `_float_or_none`, `_int_or_none`, `_str_or_none`을 `_parsing.py` 공유 모듈로 추출한다.
- **이유**: `client.py`와 `datagokr.py`에 동일 구현이 중복되어 있었다.
- **결과**: 양쪽 모듈에서 import로 대체.
