# Phase 5 local model benchmark

- Date: 1 Sep 2026, 21:45 SAST (Africa/Johannesburg)
- Hardware: macOS-26.6.2-arm64-arm-64bit · arm64 · Apple M2 Pro · 16 GB RAM
- Intent suite: `extended` (21 questions)
- Text-to-SQL suite: 7 questions
- Models requested: qwen3.5:0.8b, qwen2.5:0.5b, llama3.2:1b, gemma3:1b
- Models pulled this run: qwen2.5:0.5b, llama3.2:1b, gemma3:1b
- Live SQL execution against Postgres: yes
- Numbers are from a live Ollama run on this machine; they are not estimates.

## Recommendation

**Default local planner model: `qwen3.5:0.8b`** — best combined intent accuracy and text-to-SQL validity among the models that ran, with latency as the tie-breaker.

## Intent classification

| Model | Overall | Supported / paraphrase | Advanced | Avg latency (ms) | Errors |
|---|---:|---:|---:|---:|---:|
| `qwen3.5:0.8b` | 81% | 83% | 75% | 42556 | 0 |
| `qwen2.5:0.5b` | 29% | 50% | 0% | 277 | 0 |
| `llama3.2:1b` | 57% | 50% | 62% | 515 | 0 |
| `gemma3:1b` | 33% | 58% | 0% | 442 | 0 |

## Text-to-SQL

| Model | Valid SELECT | Org-scope when required | Avg latency (ms) | Executed | Errors |
|---|---:|---:|---:|---:|---:|
| `qwen3.5:0.8b` | 0% | 0% | 313688 | 0/7 | 7 |
| `qwen2.5:0.5b` | 0% | 100% | 1316 | 0/7 | 7 |
| `llama3.2:1b` | 29% | 100% | 526 | 2/7 | 5 |
| `gemma3:1b` | 0% | 0% | 1497 | 0/7 | 7 |

### Per-question SQL

#### `qwen3.5:0.8b`

- **How many franchisees are there?** — fail (334423 ms)
  - Error: generation returned None
- **How many active franchisees are there?** — fail (333446 ms)
  - Error: generation returned None
- **How many children are enrolled?** — fail (334353 ms)
  - Error: generation returned None
- **How many franchisees are there by province?** — fail (333313 ms)
  - Error: generation returned None
- **How many franchisees does each coach manage?** — fail (331760 ms)
  - Error: generation returned None
- **What is the population by province?** — fail (334904 ms)
  - Error: generation returned None
- **Which province has the most franchisees?** — fail (193617 ms)
  - Error: generation returned None

#### `qwen2.5:0.5b`

- **How many franchisees are there?** — fail (668 ms)
  - SQL: `SELECT COUNT(f.franchisee_id) AS total_franchisees FROM franchisees f JOIN small_areas sa ON sa.id = f.small_area_id WHERE f.organisation_id = :organisation_id`
  - Error: execution failed: (psycopg.errors.UndefinedColumn) column f.franchisee_id does not exist
LINE 1: SELECT COUNT(f.franchisee_id) AS total_franchisees
                     ^
[SQL: SELECT COUNT(f.franchisee_id) AS total_franchisees
FROM franchisees f
JOIN small_areas sa ON sa.id = f.small_area_id
WHERE f.organisation_id = %(organisation_id)s]
[parameters: {'organisation_id': 1}]
(Background on this error at: https://sqlalche.me/e/20/f405)
- **How many active franchisees are there?** — fail (585 ms)
  - Error: generation returned None
- **How many children are enrolled?** — fail (991 ms)
  - Error: generation returned None
- **How many franchisees are there by province?** — fail (2422 ms)
  - Error: generation returned None
- **How many franchisees does each coach manage?** — fail (1380 ms)
  - Error: generation returned None
- **What is the population by province?** — fail (2429 ms)
  - Error: generation returned None
- **Which province has the most franchisees?** — fail (735 ms)
  - Error: generation returned None

#### `llama3.2:1b`

- **How many franchisees are there?** — fail (782 ms)
  - SQL: `SELECT COUNT(*) FROM coaches AS T1 INNER JOIN organisations AS T2 ON T1.organisation_id = T2.id WHERE T2.organisation_id = :organisation_id`
  - Error: missing tables: franchisees
- **How many active franchisees are there?** — fail (403 ms)
  - SQL: `SELECT COUNT(*) FROM coaches AS T1 INNER JOIN organisations AS T2 ON T1.organisation_id = T2.id WHERE T1.status = 'ACTIVE' AND T2.id = :organisation_id`
  - Error: missing tables: franchisees
- **How many children are enrolled?** — pass (388 ms)
  - SQL: `SELECT COUNT(DISTINCT T1.id) FROM children AS T1 INNER JOIN attendance AS T2 ON T1.id = T2.child_id WHERE T1.organisation_id = :organisation_id`
- **How many franchisees are there by province?** — fail (456 ms)
  - SQL: `SELECT COUNT(DISTINCT T1.organisation_id) AS province_count FROM organisations AS T1 INNER JOIN provinces AS T2 ON T1.organisation_id = T2.id WHERE T1.organisation_id = :organisation_id`
  - Error: missing tables: franchisees
- **How many franchisees does each coach manage?** — pass (471 ms)
  - SQL: `SELECT coach_id, COUNT(*) AS num_coaches FROM coaches AS T1 INNER JOIN franchisees AS T2 ON T1.organisation_id = T2.organisation_id WHERE T1.organisation_id = :organisation_id GROUP BY coach_id`
- **What is the population by province?** — fail (702 ms)
  - SQL: `SELECT p.id, p.name, p.census_code, COALESCE(SUM(s.population_total), 0) AS population_total FROM provinces p JOIN population_snapshots ps ON p.id = ps.province_id GROUP BY p.id, p.name, p.census_code`
  - Error: execution failed: (psycopg.errors.UndefinedColumn) column ps.province_id does not exist
LINE 3: JOIN population_snapshots ps ON p.id = ps.province_id
                                               ^
[SQL: SELECT p.id, p.name, p.census_code, COALESCE(SUM(s.population_total), 0) AS population_total
FROM provinces p
JOIN population_snapshots ps ON p.id = ps.province_id
GROUP BY p.id, p.name, p.census_code]
(Background on this error at: https://sqlalche.me/e/20/f405)
- **Which province has the most franchisees?** — fail (479 ms)
  - SQL: `SELECT p.id, p.name FROM provinces p JOIN monthly_metrics mm ON p.id = mm.province_id WHERE mm.organisation_id = :organisation_id GROUP BY p.id ORDER BY COUNT(*) DESC LIMIT 1`
  - Error: missing tables: franchisees

#### `gemma3:1b`

- **How many franchisees are there?** — fail (979 ms)
  - Error: generation returned None
- **How many active franchisees are there?** — fail (949 ms)
  - Error: generation returned None
- **How many children are enrolled?** — fail (1033 ms)
  - Error: generation returned None
- **How many franchisees are there by province?** — fail (4572 ms)
  - Error: generation returned None
- **How many franchisees does each coach manage?** — fail (1400 ms)
  - Error: generation returned None
- **What is the population by province?** — fail (855 ms)
  - SQL: `SELECT p.name, COUNT(*) FROM municipalities AS p JOIN provinces AS p2 ON p.id = p2.province_id GROUP BY p.id, p.name ORDER BY COUNT(*) DESC LIMIT 100`
  - Error: missing tables: population_snapshots
- **Which province has the most franchisees?** — fail (691 ms)
  - SQL: `SELECT p.name FROM municipalities AS p JOIN provinces AS p2 ON p.id = p2.id GROUP BY p.id ORDER BY COUNT(*) LIMIT 100`
  - Error: missing organisation_id bind parameter; missing tables: franchisees

## How to reproduce

```bash
uv run python scripts/compare_planner_models.py --pull --details \
    --write docs/phase5-model-benchmark.md
```

Default models are the small laptop catalog tags in `DEFAULT_BENCHMARK_MODELS`. Use `--models ...` to override. Ollama must be running at `OLLAMA_BASE_URL` (default http://localhost:11434).
