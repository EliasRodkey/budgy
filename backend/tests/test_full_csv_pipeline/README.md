# CSV Pipeline Integration Tests

End-to-end AI integration tests for the CSV upload pipeline. Runs real Claude API calls against 9 fixture CSVs and scores each stage.

## Running

```bash
pytest backend/tests/test_full_csv_pipeline/ -m ai_integration -v -s \
  --run-description "what changed in this run"
```

`--run-description` labels the run in the results CSV so you can track what prompt or code change each run corresponds to. Omit it and the description column will be blank.

Requires `ANTHROPIC_API_KEY` in the environment (loaded from `.env` via `pytest-dotenv`).

## Fixtures

| fixture | what it covers |
| --- | --- |
| `sofi_happy_path` | Clean SoFi export, standard columns |
| `chase` | Chase CSV format |
| `apple_card` | Apple Card export |
| `mint` | Mint export with category column |
| `adversarial_delimiter` | Non-comma delimiter |
| `adversarial_personal` | Personal/non-standard column names |
| `adversarial_structural` | Structural quirks (extra rows, blank lines) |
| `adversarial_encoding` | Encoding edge cases |
| `adversarial_aggregator` | Aggregator-style export with many extra columns (Posted Date, Merchant, Type, Sub-category, Running Balance, Payment Method) — tests that the AI correctly maps only the relevant fields and ignores noise |

Each fixture has a paired `.expected.json` sidecar that defines the ideal normalization plan and expected output rows used for scoring.

## Results

Two outputs are written after every run:

- **`results/results.csv`** — growing table, one row per fixture per run. Columns: `timestamp`, `model`, `description`, `fixture_name`, `column_map_score`, `category_map_score`, `amount_transform_score`, `row_score`, `overall_score`. Open in a spreadsheet to compare runs over time.

- **`results/runs/<timestamp>.json`** — full stage-by-stage detail for a single run. The timestamp matches the `pleasant_loggers` log file timestamp so runs can be correlated with application logs.

The test only fails pytest on fatal pipeline errors (exceptions, job failure, unexpected unmapped required columns). Score regressions are visible in the CSV but do not fail the suite.
