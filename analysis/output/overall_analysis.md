# Overall Analysis


## (a) Cross-session & Cross-benchmark Analysis

### Benchmark Comparison

| Benchmark | Sessions | Avg Cost | Avg Errors | Avg Redundant | Avg Repeated Mods | Avg Rollback | Avg Cache Hit |
|-----------|----------|----------|------------|---------------|-------------------|--------------|---------------|
| bigcodebench | 17 | $0.0779 | 1.8 | 0.2 | 0.1 | 0.0 | 0.974 |
| open | 7 | $0.8360 | 1.9 | 0.3 | 1.0 | 0.0 | 0.914 |
| swebench | 33 | $1.6593 | 4.1 | 1.7 | 2.2 | 0.0 | 0.984 |
| terminalbench | 20 | $0.9655 | 4.2 | 0.8 | 2.2 | 0.1 | 0.891 |

### Error Type Distribution by Benchmark

| Benchmark | Total Errors | Syntax | NotFound | TestFailed | Timeout | Other |
|-----------|-------------|--------|----------|------------|---------|-------|
| bigcodebench | 30 | 0 | 16 | 0 | 0 | 14 |
| open | 13 | 0 | 5 | 0 | 0 | 8 |
| swebench | 134 | 4 | 51 | 4 | 0 | 75 |
| terminalbench | 83 | 0 | 32 | 2 | 0 | 49 |

### Metric Relationships

(Note: with small n, these are observations, not statistically robust correlations)

- Sessions with error_rate>0.2: avg repeated_file_modifications=0.4 (vs 2.0 for error_rate<=0.2)
  (n=17 high-error sessions, n=60 low-error sessions)
- High cache hit (>0.5): avg cost=$1.0672 (vs $0.1311 for low cache)

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
| cat | 493 | 0.08 | 869 | 10135 |
| python3 | 374 | 0.06 | 1191 | 9838 |
| git-log | 338 | 0.00 | 586 | 4754 |
| grep | 229 | 0.01 | 491 | 5936 |
| python-c | 193 | 0.15 | 291 | 9530 |
| ls | 167 | 0.08 | 653 | 6752 |
| find | 150 | 0.01 | 651 | 5714 |
| cd | 111 | 0.19 | 790 | 6397 |
| git-show | 83 | 0.00 | 929 | 6404 |
| pytest | 60 | 0.48 | 1622 | 4402 |
| # | 49 | 0.00 | 383 | 7436 |
| docker | 38 | 0.11 | 1237 | 4178 |
| mkdir | 33 | 0.27 | 54 | 9801 |
| git-diff | 31 | 0.00 | 1083 | 6728 |
| which | 30 | 0.20 | 53 | 4800 |
| pwd | 30 | 0.00 | 851 | 9360 |
| echo | 27 | 0.04 | 531 | 10944 |
| pip | 21 | 0.19 | 307 | 3407 |
| git-branch | 19 | 0.00 | 53 | 4012 |
| git-tag | 19 | 0.00 | 52 | 4390 |

### By error rate (min 3 calls)

| Command | Count | Errors | Error Rate |
|---------|-------|--------|------------|
| python | 11 | 11 | 1.00 |
| sudo | 13 | 9 | 0.69 |
| git-describe | 3 | 2 | 0.67 |
| pytest | 60 | 29 | 0.48 |
| django | 7 | 2 | 0.29 |
| mkdir | 33 | 9 | 0.27 |
| base64 | 4 | 1 | 0.25 |
| export | 8 | 2 | 0.25 |
| which | 30 | 6 | 0.20 |
| head | 5 | 1 | 0.20 |
| cp | 5 | 1 | 0.20 |
| configure | 5 | 1 | 0.20 |
| pip | 21 | 4 | 0.19 |
| cd | 111 | 21 | 0.19 |
| sed | 18 | 3 | 0.17 |
| python-c | 193 | 29 | 0.15 |
| rm | 15 | 2 | 0.13 |
| docker | 38 | 4 | 0.11 |
| cat | 493 | 39 | 0.08 |
| ls | 167 | 13 | 0.08 |
| python3 | 374 | 24 | 0.06 |
| echo | 27 | 1 | 0.04 |
| find | 150 | 2 | 0.01 |
| grep | 229 | 3 | 0.01 |
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
| git-clone | 2 |
| git-rev-list | 1 |
| git-fetch | 1 |
| git-merge-base | 1 |
| git-rev-parse | 1 |
| git-stash | 1 |
| git-checkout | 1 |
| git-submodule | 1 |


## (c) Per-benchmark Tool Profiles


### bigcodebench (107 tool calls)

**Tool distribution:**
  - Bash: 76 (71.0%)
  - Read: 17 (15.9%)
  - Edit: 14 (13.1%)

**Action class distribution:**
  - file_modify: 45 (42.1%)
  - exec_test: 28 (26.2%)
  - read: 17 (15.9%)
  - search: 12 (11.2%)
  - other: 5 (4.7%)

**Top commands:**
  - cat: 31
  - python3: 22
  - ls: 12
  - python: 6
  - pip3: 2
  - pip: 1
  - pkill: 1
  - which: 1

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

### terminalbench (871 tool calls)

**Tool distribution:**
  - Bash: 800 (91.8%)
  - Read: 36 (4.1%)
  - Edit: 35 (4.0%)

**Action class distribution:**
  - other: 336 (38.6%)
  - file_modify: 226 (25.9%)
  - search: 140 (16.1%)
  - read: 95 (10.9%)
  - exec_test: 70 (8.0%)
  - vcs: 3 (0.3%)
  - rollback: 1 (0.1%)

**Top commands:**
  - cat: 211
  - ls: 97
  - python3: 69
  - #: 49
  - docker: 38
  - mkdir: 31
  - cd: 31
  - find: 22
  - which: 20
  - echo: 19


## Limitations & Caveats

- result_len is character length, not tokens. Token proxy only.
- read_but_unused_files measures 'not modified', not 'not referenced in reasoning'.
- error_type is keyword heuristic, not 100% accurate.
- TestFailed may be normal debugging, not inefficiency.
- latency_ms mixes model inference wait + tool execution time; cannot separate.
- cache_hit_ratio: calls with input_tokens=0 and high cache_read are normal (multi-turn cache).
- Small n per benchmark type — observations are tentative, not generalizable.
- Sessions with read_but_unused_files=N/A (due to patch/git apply): 0/77