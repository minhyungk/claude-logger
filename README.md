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
│       ├── swebench/       # SWE-bench Lite 통합 (300개)
│       ├── terminalbench/  # TerminalBench (200개)
│       ├── intercode/      # InterCode (bash/python/sql)
│       └── bigcodebench/   # BigCodeBench
├── runner/         # 벤치마크 디스커버리 & 실행기
│   ├── discovery.py    # 벤치마크 자동 탐색
│   └── executor.py     # Claude Code 실행 + workspace 관리
├── analysis/       # 로그 비효율 분석
│   ├── analyze.py      # 분석 스크립트 (단계별 실행)
│   └── output/         # 분석 결과물 (gitignored)
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
| `--filter-type` | 벤치마크 종류 필터 (`open`, `swebench`, `terminalbench`, `intercode`, `bigcodebench`) | 전체 |
| `--swebench-limit N` | SWE-bench 인스턴스 수 제한 | 전체(300) |
| `--swebench-ids` | 콤마 구분 인스턴스 ID 필터 | 없음 |
| `--terminalbench-limit N` | TerminalBench 태스크 수 제한 | 전체(200) |
| `--terminalbench-ids` | 콤마 구분 TerminalBench 태스크 ID 필터 | 없음 |
| `--no-viz` | 벤치마크만 실행 (대시보드 생략) | off |
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

## 로그 분석

벤치마크 실행 후 생성된 로그에서 에이전트 비효율 패턴(토큰 낭비, 반복 작업, 자기수정 루프 등)을 추출:

```bash
# 단계 0: 데이터 검증 (먼저 이것만 실행, 결과 확인 후 다음 단계)
python3 analysis/analyze.py --stage 0

# 단계 1: events.jsonl 생성 (tool 호출 단위 플랫 데이터)
python3 analysis/analyze.py --stage 1

# 단계 2: session_metrics.csv 생성 (세션 단위 집계)
python3 analysis/analyze.py --stage 2

# 단계 3: per_session_analysis.md (비효율 세션 상세 분석)
python3 analysis/analyze.py --stage 3

# 단계 4: overall_analysis.md (전체 교차 분석)
python3 analysis/analyze.py --stage 4
```

### 분석 출력물

| 파일 | 설명 |
|------|------|
| `analysis/output/stage0_validation.json` | 벤치별 파싱 검증 리포트 |
| `analysis/output/events.jsonl` | 모든 tool 호출 (1행 = 1 tool_use). 세션 간 비교, 필터링, 집계에 사용 |
| `analysis/output/session_metrics.csv` | 세션별 집계 지표 (비용, 에러율, 중복호출, 반복수정, rollback 등) |
| `analysis/output/per_session_analysis.md` | 비효율 상위 세션의 trace 기반 근거 |
| `analysis/output/overall_analysis.md` | 벤치별/도구별/명령별 교차 분석 |

### 분석 옵션

```bash
# 다른 로그 디렉토리 지정
python3 analysis/analyze.py --stage 1 --logs-dir /path/to/other/logs
```

### 추출되는 주요 지표

- **redundant_tool_calls**: 동일 입력으로 반복 호출된 도구 수
- **repeated_file_modifications**: 같은 파일을 여러 번 수정 (자기수정 루프 신호)
- **rollback_count**: git checkout/reset (완전 원복 = 명확한 헛수고)
- **error_rate / error_breakdown**: 에러 비율 및 유형별 분류 (Syntax, NotFound, TestFailed, Timeout)
- **max_consecutive_errors**: 연속 에러 최대 길이
- **read_but_unused_files**: Read 했으나 수정 대상이 되지 않은 파일 수
- **occupancy_growth**: 컨텍스트 윈도우 점유율 증가폭
- **average_cache_hit_ratio**: 캐시 히트율 (비용 효율 지표)

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
