# claude-logger

Claude Code의 API 호출을 투명하게 프록시하여 로깅하고, 벤치마크 실행 결과를 시각화하는 도구.

## 구조

```
claude-logger/
├── proxy/          # API 프록시 서버
│   ├── server.py       # Direct API 프록시 (ANTHROPIC_API_KEY 사용)
│   ├── bedrock.py      # Bedrock 프록시 (AWS 인증 패스스루)
│   ├── logger.py       # 호출 로거 (JSON 기록)
│   ├── pricing.py      # 모델별 비용 계산
│   └── sse_parser.py   # SSE/EventStream 파서
├── benchmarks/     # 벤치마크 정의
│   ├── open/           # 자유 형식 벤치마크 (JSON 기반, 16개)
│   └── external/
│       └── swebench/   # SWE-bench Lite 통합 (300개)
├── runner/         # 벤치마크 디스커버리 & 실행기
│   ├── discovery.py    # 벤치마크 자동 탐색
│   └── executor.py     # Claude Code 실행 + workspace 관리
└── viz/            # 대시보드 (세션별 토큰, 비용, 지연시간 차트)
```

## 설치

```bash
pip install -r requirements.txt
```

## 빠른 시작

### 1. 벤치마크 실행 (Bedrock)

API 키 없이, 기존 AWS Bedrock 인증을 그대로 사용:

```bash
python3 main.py --bedrock --model sonnet --benchmark chess-engine --swebench-limit 0
```

### 2. 대시보드 확인

```bash
python3 main.py --viz-only
```

`http://127.0.0.1:8090` 에서 결과 확인.

### 3. 벤치마크 + 대시보드 동시 실행

터미널 두 개에서:

```bash
# 터미널 1: 대시보드
python3 main.py --viz-only --log-dir logs

# 터미널 2: 벤치마크
python3 main.py --bedrock --model sonnet --benchmark chess-engine --swebench-limit 0 --log-dir logs
```

## CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--bedrock` | Bedrock 프록시 모드 (API 키 불필요) | off |
| `--model` | 사용할 모델 (`sonnet`, `opus`, `haiku`) | 환경 기본값 |
| `--port` | 프록시 서버 포트 | 8080 |
| `--viz-port` | 대시보드 포트 | 8090 |
| `--log-dir` | 로그 저장 디렉토리 | `logs/` |
| `--benchmark` | 이름 필터 (부분 매칭) | 전체 |
| `--swebench-limit N` | SWE-bench 인스턴스 수 제한 | 전체(300) |
| `--swebench-ids` | 콤마 구분 인스턴스 ID 필터 | 없음 |
| `--viz-only` | 대시보드만 실행 | off |

## 인증 모드

### Bedrock (권장)

환경에 `CLAUDE_CODE_USE_BEDROCK=1`과 `AWS_BEARER_TOKEN_BEDROCK`이 설정돼 있으면 그대로 사용. 별도 설정 불필요:

```bash
python3 main.py --bedrock --model sonnet --benchmark chess-engine --swebench-limit 0
```

### Direct API

`.env` 파일에 API 키를 설정:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

```bash
python3 main.py --model sonnet --benchmark chess-engine --swebench-limit 0
```

## 출력 구조

각 벤치마크 실행 후 세션 디렉토리:

```
logs/session_chess-engine_abc12345/
├── call_001.json       # API 호출 로그 (토큰, 비용, 지연시간, 대화내용)
├── call_002.json       # 멀티턴 호출
├── stdout.txt          # Claude 텍스트 출력
├── stderr.txt          # 에러 출력 (있을 경우)
└── workspace/          # Claude가 생성한 파일들
    ├── chess.py
    └── ...
```

### call_*.json 내용

```json
{
  "meta": { "model": "...", "session_id": "...", "call_index": 1, "timestamp": "..." },
  "tokens": { "input_tokens": 300, "output_tokens": 1500, "cache_read_input_tokens": 0 },
  "cost": { "input_cost": 0.0009, "output_cost": 0.0225, "total_cost": 0.0234 },
  "context": { "occupancy_pct": 0.15, "num_turns": 1 },
  "tools": [{ "name": "Write", "input": {...} }],
  "performance": { "latency_ms": 4500, "stop_reason": "end_turn" },
  "conversation": { "messages": [...], "assistant_response": "..." }
}
```

## 벤치마크

### Open 벤치마크 (16개)

`benchmarks/open/` 디렉토리의 JSON 파일들. 자동 채점 없이 생성된 코드만 보존:

- chess-engine, regex-engine, rsa-encryption
- tetris-html5, pathfinding-visualizer, sudoku-generator-solver
- kv-store, simple-shell, roguelike-dungeon
- markdown-parser, tcp-chat-server, huffman-compression
- static-site-generator, file-encryption-tool, terminal-weather-app
- tetris-01 (pygame)

```bash
# 특정 벤치마크만
python3 main.py --bedrock --model sonnet --benchmark regex --swebench-limit 0

# 전체 open 벤치마크
python3 main.py --bedrock --model sonnet --swebench-limit 0
```

### SWE-bench Lite (300개)

[SWE-bench Lite](https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite) — 실제 GitHub 이슈를 해결하는 능력 측정. 레포 clone → base_commit checkout → Claude에게 문제 전달 → test patch로 pass/fail 판정:

```bash
# 특정 인스턴스
python3 main.py --bedrock --model sonnet --swebench-ids "django__django-11099"

# 상위 5개만
python3 main.py --bedrock --model sonnet --swebench-limit 5

# swebench만 필터
python3 main.py --bedrock --model sonnet --benchmark swebench
```

### 커스텀 벤치마크 추가

`benchmarks/open/` 에 JSON 파일 추가:

```json
{
  "name": "my-benchmark",
  "type": "open",
  "prompt": "Build a REST API with FastAPI that ...",
  "description": "Tests API design ability"
}
```

## 대시보드

세션별로:
- 토큰 분류 차트 (input / output / cache read / cache write)
- 컨텍스트 윈도우 점유율 추이
- 누적 비용 그래프
- 지연 시간 분포
- 도구 사용 빈도
- 개별 호출 상세 조회 (클릭)

## 동작 원리

```
Claude Code ──→ Local Proxy (port 8080) ──→ Bedrock / Anthropic API
                     │
                     ▼
              logs/session_*/call_*.json
```

- **Bedrock 모드**: `ANTHROPIC_BEDROCK_BASE_URL`을 로컬 프록시로 설정 → AWS 인증 헤더 패스스루 → 실제 Bedrock에 전달
- **Direct 모드**: `ANTHROPIC_BASE_URL`을 프록시로 설정 → API 키로 인증 → `api.anthropic.com`에 전달
- Claude Code는 `--dangerously-skip-permissions`로 실행돼 workspace에 직접 파일 생성
