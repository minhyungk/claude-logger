# Per-Session Analysis


## swebench-django__django-11283_dffa3dce

- Benchmark: swebench
- Total calls: 108, Tool uses: 107
- Cost: $2.524624, Latency: 716.71s
- Errors: 6 (rate: 0.0561)
  - Syntax: 0, NotFound: 0, TestFailed: 0, Timeout: 0
- Redundant calls: 7
- Repeated file modifications: 28
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 2
- Cache hit ratio: 0.9906
- Occupancy: max=42.12%, growth=40.27%
- Read but unused files: 2

### Error sequences (1 sequences of 2+ consecutive errors)

  Sequence 1 (turns 25-26):
    - [Bash] python3 → Other
    - [Bash] cat → Other

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11283_dffa3dce/workspace/swebench_workspaces/django__django-11283/django/contrib/auth/migrations/0011_update_proxy_permissions.py: 21 times
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11283_dffa3dce/workspace/swebench_workspaces/django__django-11283/tests/auth_tests/test_migrations.py: 9 times


## swebench-django__django-11910_d42bfadc

- Benchmark: swebench
- Total calls: 141, Tool uses: 140
- Cost: $5.091065, Latency: 1222.95s
- Errors: 8 (rate: 0.0571)
  - Syntax: 0, NotFound: 1, TestFailed: 0, Timeout: 0
- Redundant calls: 5
- Repeated file modifications: 10
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 3
- Cache hit ratio: 0.9999
- Occupancy: max=68.63%, growth=67.43%
- Read but unused files: 4

### Error sequences (1 sequences of 2+ consecutive errors)

  Sequence 1 (turns 11-13):
    - [Bash] cd → Other
    - [Bash] cat → Other
    - [Read] ./tests/migrations/test_autodetector.py → Other

### Repeated file modifications
  - ./django/db/migrations/autodetector.py: 11 times


## swebench-django__django-12113_daa27f7b

- Benchmark: swebench
- Total calls: 113, Tool uses: 114
- Cost: $5.318163, Latency: 1162.59s
- Errors: 8 (rate: 0.0702)
  - Syntax: 0, NotFound: 3, TestFailed: 1, Timeout: 0
- Redundant calls: 3
- Repeated file modifications: 4
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 1
- Cache hit ratio: 0.9823
- Occupancy: max=47.95%, growth=45.73%
- Read but unused files: 9

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-12113_daa27f7b/workspace/swebench_workspaces/django__django-12113/django/db/backends/sqlite3/creation.py: 5 times


## swebench-django__django-11564_6a1d3bf4

- Benchmark: swebench
- Total calls: 56, Tool uses: 55
- Cost: $1.155117, Latency: 342.61s
- Errors: 5 (rate: 0.0909)
  - Syntax: 1, NotFound: 1, TestFailed: 0, Timeout: 0
- Redundant calls: 2
- Repeated file modifications: 5
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 1
- Cache hit ratio: 0.9997
- Occupancy: max=31.16%, growth=28.82%
- Read but unused files: 3

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11564_6a1d3bf4/workspace/swebench_workspaces/django__django-11564/django/templatetags/static.py: 3 times
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11564_6a1d3bf4/workspace/swebench_workspaces/django__django-11564/django/core/files/storage/filesystem.py: 3 times
  - /tmp/test_real_world_scenario.py: 2 times


## swebench-django__django-11964_b1ddf31a

- Benchmark: swebench
- Total calls: 65, Tool uses: 65
- Cost: $1.364267, Latency: 427.53s
- Errors: 1 (rate: 0.0154)
  - Syntax: 0, NotFound: 1, TestFailed: 0, Timeout: 0
- Redundant calls: 3
- Repeated file modifications: 7
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 1
- Cache hit ratio: 0.9692
- Occupancy: max=15.82%, growth=13.74%
- Read but unused files: 3

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11964_b1ddf31a/workspace/swebench_workspaces/django__django-11964/django/db/models/query_utils.py: 7 times
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11964_b1ddf31a/workspace/swebench_workspaces/django__django-11964/django/db/models/fields/__init__.py: 2 times


## terminalbench-advanced-poker-hand-classifier_b6c087b2

- Benchmark: terminalbench
- Total calls: 56, Tool uses: 55
- Cost: $1.666493, Latency: 711.28s
- Errors: 2 (rate: 0.0364)
  - Syntax: 0, NotFound: 0, TestFailed: 0, Timeout: 0
- Redundant calls: 1
- Repeated file modifications: 7
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 2
- Cache hit ratio: 0.9819
- Occupancy: max=34.36%, growth=31.97%
- Read but unused files: 1

### Error sequences (1 sequences of 2+ consecutive errors)

  Sequence 1 (turns 2-3):
    - [Bash] ls → Other
    - [Bash] mkdir → Other

### Repeated file modifications
  - poker_classifier.py: 8 times


## swebench-astropy__astropy-12907_3caee9e6

- Benchmark: swebench
- Total calls: 54, Tool uses: 53
- Cost: $1.267767, Latency: 465.13s
- Errors: 7 (rate: 0.1321)
  - Syntax: 0, NotFound: 2, TestFailed: 0, Timeout: 0
- Redundant calls: 1
- Repeated file modifications: 3
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 2
- Cache hit ratio: 0.9812
- Occupancy: max=32.94%, growth=31.7%
- Read but unused files: 0

### Error sequences (2 sequences of 2+ consecutive errors)

  Sequence 1 (turns 3-4):
    - [Bash] cat → NotFound
    - [Bash] python3 → Other

  Sequence 2 (turns 18-19):
    - [Bash] cd → NotFound
    - [Bash] python3 → Other

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-astropy__astropy-12907_3caee9e6/workspace/swebench_workspaces/astropy__astropy-12907/astropy/modeling/separable.py: 4 times


## swebench-django__django-11001_f35dcabd

- Benchmark: swebench
- Total calls: 63, Tool uses: 62
- Cost: $1.54717, Latency: 419.34s
- Errors: 4 (rate: 0.0645)
  - Syntax: 0, NotFound: 2, TestFailed: 0, Timeout: 0
- Redundant calls: 4
- Repeated file modifications: 3
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 1
- Cache hit ratio: 0.9997
- Occupancy: max=37.91%, growth=35.7%
- Read but unused files: 0

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11001_f35dcabd/workspace/swebench_workspaces/django__django-11001/tests/queries/test_sqlcompiler.py: 3 times
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11001_f35dcabd/workspace/swebench_workspaces/django__django-11001/django/db/models/sql/compiler.py: 2 times


## swebench-django__django-11179_08596755

- Benchmark: swebench
- Total calls: 51, Tool uses: 50
- Cost: $1.164376, Latency: 497.34s
- Errors: 6 (rate: 0.12)
  - Syntax: 0, NotFound: 3, TestFailed: 0, Timeout: 0
- Redundant calls: 0
- Repeated file modifications: 3
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 2
- Cache hit ratio: 0.9996
- Occupancy: max=30.72%, growth=29.52%
- Read but unused files: 2

### Error sequences (1 sequences of 2+ consecutive errors)

  Sequence 1 (turns 24-25):
    - [Bash] python-c → NotFound
    - [Bash] python-c → NotFound

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_swebench-django__django-11179_08596755/workspace/swebench_workspaces/django__django-11179/django/db/models/deletion.py: 4 times


## rsa-encryption_1711795e

- Benchmark: open
- Total calls: 29, Tool uses: 31
- Cost: $1.075775, Latency: 586.38s
- Errors: 4 (rate: 0.129)
  - Syntax: 0, NotFound: 1, TestFailed: 0, Timeout: 0
- Redundant calls: 1
- Repeated file modifications: 3
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 3
- Cache hit ratio: 0.9994
- Occupancy: max=29.45%, growth=14.14%
- Read but unused files: 0

### Error sequences (1 sequences of 2+ consecutive errors)

  Sequence 1 (turns 1-3):
    - [Bash] python → NotFound
    - [Bash] python3 → Other
    - [Edit] /Users/michaelkwon/Desktop/AegisData/cla → Other

### Repeated file modifications
  - /Users/michaelkwon/Desktop/AegisData/claude-logger/logs/session_regex-engine_86265389/workspace/regex_engine.py: 3 times
  - test_regex_engine.py: 2 times


## swebench-django__django-11099_b2a72280

- Benchmark: swebench
- Total calls: 35, Tool uses: 34
- Cost: $0.431179, Latency: 208.91s
- Errors: 6 (rate: 0.1765)
  - Syntax: 2, NotFound: 2, TestFailed: 0, Timeout: 0
- Redundant calls: 3
- Repeated file modifications: 1
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 3
- Cache hit ratio: 0.9709
- Occupancy: max=14.24%, growth=13.17%
- Read but unused files: 1

### Error sequences (2 sequences of 2+ consecutive errors)

  Sequence 1 (turns 12-14):
    - [Bash] pytest → NotFound
    - [Bash] pytest → Other
    - [Bash] django → NotFound

  Sequence 2 (turns 16-17):
    - [Bash] cd → Syntax
    - [Bash] cd → Syntax

### Repeated file modifications
  - ./django/contrib/auth/validators.py: 2 times


## swebench-astropy__astropy-6938_3c830c98

- Benchmark: swebench
- Total calls: 83, Tool uses: 82
- Cost: $2.035948, Latency: 512.39s
- Errors: 7 (rate: 0.0854)
  - Syntax: 0, NotFound: 3, TestFailed: 0, Timeout: 0
- Redundant calls: 3
- Repeated file modifications: 0
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 2
- Cache hit ratio: 0.9877
- Occupancy: max=39.39%, growth=38.25%
- Read but unused files: 2

### Error sequences (2 sequences of 2+ consecutive errors)

  Sequence 1 (turns 5-6):
    - [Bash] pytest → NotFound
    - [Bash] pytest → NotFound

  Sequence 2 (turns 10-11):
    - [Bash] pytest → Other
    - [Bash] pytest → Other


## swebench-django__django-12184_fee4a485

- Benchmark: swebench
- Total calls: 242, Tool uses: 244
- Cost: $11.935538, Latency: 2209.47s
- Errors: 8 (rate: 0.0328)
  - Syntax: 0, NotFound: 5, TestFailed: 1, Timeout: 0
- Redundant calls: 1
- Repeated file modifications: 0
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 1
- Cache hit ratio: 0.971
- Occupancy: max=66.98%, growth=65.51%
- Read but unused files: 6


## swebench-django__django-10924_f9b88d8b

- Benchmark: swebench
- Total calls: 54, Tool uses: 53
- Cost: $0.800302, Latency: 306.95s
- Errors: 6 (rate: 0.1132)
  - Syntax: 0, NotFound: 1, TestFailed: 0, Timeout: 0
- Redundant calls: 1
- Repeated file modifications: 1
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 2
- Cache hit ratio: 0.981
- Occupancy: max=20.13%, growth=17.56%
- Read but unused files: 2

### Error sequences (2 sequences of 2+ consecutive errors)

  Sequence 1 (turns 9-10):
    - [Bash] pytest → NotFound
    - [Bash] pytest → Other

  Sequence 2 (turns 13-14):
    - [Bash] python-c → Other
    - [Bash] python-c → Other

### Repeated file modifications
  - /tmp/test_final_verification.py: 2 times


## terminalbench-advanced-json-to-rfc4180-csv-converter_dbd598c8

- Benchmark: terminalbench
- Total calls: 39, Tool uses: 43
- Cost: $0.873422, Latency: 395.8s
- Errors: 3 (rate: 0.0698)
  - Syntax: 0, NotFound: 0, TestFailed: 0, Timeout: 0
- Redundant calls: 1
- Repeated file modifications: 3
- Rollbacks: 0, Stashes: 0
- Max consecutive errors: 1
- Cache hit ratio: 0.9995
- Occupancy: max=24.31%, growth=22.22%
- Read but unused files: 0

### Repeated file modifications
  - demo_exact_paths.py: 3 times
  - converter.py: 2 times
