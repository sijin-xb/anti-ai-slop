# 온보딩 가이드

## 저장소 준비

```bash
git clone https://example.com/team/collector.git
cd collector && make bootstrap
```

`make bootstrap`는 가상환경을 만들고 의존성을 설치합니다. Python 3.12 이상이 필요합니다.

## 로컬 실행

설정 파일은 `configs/local.toml`에 두고, 필수 항목은 `listen_addr`과 `log_level` 두 가지입니다.
나머지 항목은 기본값으로 동작합니다.

| 항목 | 기본값 | 설명 |
|---|---|---|
| `listen_addr` | 없음 | 수신 대기 주소 |
| `log_level` | `info` | 로그 수준 |

## 검증

부팅 후 `/healthz`가 200을 반환하면 준비가 끝난 것입니다.
샘플 이벤트는 `fixtures/events/sample.jsonl`에서 가져와 `--input`으로 넣습니다.
