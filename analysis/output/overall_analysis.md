# Overall Analysis


## (a) Cross-session & Cross-benchmark Analysis

### Benchmark Comparison

| Benchmark | Sessions | Avg Cost | Avg Errors | Avg Redundant | Avg Repeated Mods | Avg Rollback | Avg Cache Hit |
|-----------|----------|----------|------------|---------------|-------------------|--------------|---------------|
| open | 7 | $0.8360 | 1.9 | 0.3 | 1.0 | 0.0 | 0.914 |
| swebench | 33 | $1.6593 | 4.1 | 1.7 | 2.2 | 0.0 | 0.984 |
| terminalbench | 5 | $0.8510 | 2.4 | 0.8 | 3.0 | 0.0 | 0.990 |

### Error Type Distribution by Benchmark

| Benchmark | Total Errors | Syntax | NotFound | TestFailed | Timeout | Other |
|-----------|-------------|--------|----------|------------|---------|-------|
| open | 13 | 0 | 5 | 0 | 0 | 8 |
| swebench | 134 | 4 | 51 | 4 | 0 | 75 |
| terminalbench | 12 | 0 | 1 | 0 | 0 | 11 |

### Metric Relationships

(Note: with small n, these are observations, not statistically robust correlations)

- Sessions with error_rate>0.2: avg repeated_file_modifications=2.0 (vs 2.1 for error_rate<=0.2)
  (n=1 high-error sessions, n=44 low-error sessions)
- High cache hit (>0.5): avg cost=$1.4712 (vs $0.1311 for low cache)

### Time vs Tokens
(latency_ms = model inference + tool execution, mixed; cannot separate)

- swebench-django__django-12184_fee4a485: 2209.5s, $11.9355, 244 tools
- swebench-django__django-11910_d42bfadc: 1223.0s, $5.0911, 140 tools
- swebench-django__django-12113_daa27f7b: 1162.6s, $5.3182, 114 tools
- swebench-django__django-11999_c1ed441f: 1092.4s, $2.5182, 69 tools
- jwt-jws-engine_2a5e2fb7: 941.4s, $1.8916, 42 tools


## (b) cmd_program Analysis (Bash only)

### By frequency

| Command | Count | Error Rate | Avg Result Len | Avg Latency(ms) |
|---------|-------|------------|----------------|-----------------|
| git-log | 338 | 0.00 | 586 | 4754 |
| python3 | 332 | 0.05 | 1271 | 9963 |
| cat | 307 | 0.08 | 1063 | 11310 |
| grep | 212 | 0.01 | 499 | 6121 |
| python-c | 188 | 0.14 | 278 | 9136 |
| find | 136 | 0.01 | 697 | 4843 |
| git-show | 83 | 0.00 | 929 | 6404 |
| ls | 82 | 0.11 | 756 | 7114 |
| cd | 81 | 0.15 | 619 | 7021 |
| pytest | 59 | 0.49 | 1528 | 4418 |
| git-diff | 31 | 0.00 | 1083 | 6728 |
| git-branch | 19 | 0.00 | 53 | 4012 |
| git-tag | 19 | 0.00 | 52 | 4390 |
| pwd | 15 | 0.00 | 1417 | 7606 |
| pip | 15 | 0.07 | 291 | 3726 |
| sed | 13 | 0.23 | 613 | 7173 |
| echo | 12 | 0.00 | 554 | 12066 |
| git-blame | 12 | 0.00 | 1691 | 5056 |
| git-status | 11 | 0.00 | 263 | 5973 |
| which | 11 | 0.00 | 53 | 4915 |

### By error rate (min 3 calls)

| Command | Count | Errors | Error Rate |
|---------|-------|--------|------------|
| python | 5 | 5 | 1.00 |
| git-describe | 3 | 2 | 0.67 |
| pytest | 59 | 29 | 0.49 |
| mkdir | 9 | 3 | 0.33 |
| django | 7 | 2 | 0.29 |
| cp | 4 | 1 | 0.25 |
| base64 | 4 | 1 | 0.25 |
| sed | 13 | 3 | 0.23 |
| cd | 81 | 12 | 0.15 |
| python-c | 188 | 26 | 0.14 |
| ls | 82 | 9 | 0.11 |
| cat | 307 | 25 | 0.08 |
| pip | 15 | 1 | 0.07 |
| python3 | 332 | 17 | 0.05 |
| find | 136 | 2 | 0.01 |
| grep | 212 | 2 | 0.01 |
| git-log | 338 | 1 | 0.00 |

### Git subcommands

| Subcommand | Count |
|------------|-------|
| git-log | 338 |
| git-show | 83 |
| git-diff | 31 |
| git-branch | 19 |
| git-tag | 19 |
| git-blame | 12 |
| git-status | 11 |
| git-remote | 5 |
| git-describe | 3 |
| git-rev-list | 1 |
| git-fetch | 1 |
| git-merge-base | 1 |
| git-rev-parse | 1 |
| git-stash | 1 |


## (c) Per-benchmark Tool Profiles


### open (138 tool calls)

**Tool distribution:**
  - Bash: 126 (91.3%)
  - Edit: 8 (5.8%)
  - Read: 4 (2.9%)

**Action class distribution:**
  - file_modify: 72 (52.2%)
  - exec_test: 24 (17.4%)
  - other: 21 (15.2%)
  - read: 13 (9.4%)
  - search: 8 (5.8%)

**Top commands:**
  - cat: 72
  - python3: 21
  - echo: 8
  - ls: 7
  - python: 3
  - cd: 2
  - mkdir: 2
  - chmod: 2
  - curl: 2
  - sleep: 2

### swebench (2222 tool calls)

**Tool distribution:**
  - Bash: 1766 (79.5%)
  - Read: 353 (15.9%)
  - Edit: 103 (4.6%)

**Action class distribution:**
  - vcs: 523 (23.5%)
  - search: 389 (17.5%)
  - read: 383 (17.2%)
  - other: 342 (15.4%)
  - exec_test: 320 (14.4%)
  - file_modify: 264 (11.9%)
  - rollback: 1 (0.0%)

**Top commands:**
  - git-log: 338
  - python3: 262
  - grep: 211
  - python-c: 181
  - cat: 179
  - find: 127
  - git-show: 83
  - cd: 78
  - pytest: 59
  - ls: 51

### terminalbench (213 tool calls)

**Tool distribution:**
  - Bash: 192 (90.1%)
  - Read: 13 (6.1%)
  - Edit: 8 (3.8%)

**Action class distribution:**
  - file_modify: 54 (25.4%)
  - exec_test: 49 (23.0%)
  - other: 47 (22.1%)
  - search: 35 (16.4%)
  - read: 28 (13.1%)

**Top commands:**
  - cat: 56
  - python3: 49
  - ls: 24
  - find: 8
  - mkdir: 7
  - python-c: 6
  - hexdump: 5
  - echo: 4
  - pwd: 4
  - file: 4


## Limitations & Caveats

- result_len is character length, not tokens. Token proxy only.
- read_but_unused_files measures 'not modified', not 'not referenced in reasoning'.
- error_type is keyword heuristic, not 100% accurate.
- TestFailed may be normal debugging, not inefficiency.
- latency_ms mixes model inference wait + tool execution time; cannot separate.
- cache_hit_ratio: calls with input_tokens=0 and high cache_read are normal (multi-turn cache).
- Small n per benchmark type — observations are tentative, not generalizable.
- Sessions with read_but_unused_files=N/A (due to patch/git apply): 0/45