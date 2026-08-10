# SUUMO EDA and Cleaning Findings

Dataset snapshot: latest 180 source batches retrieved on 2026-08-09.

## Dataset outputs

| Dataset | Rows | Columns | Purpose |
|---|---:|---:|---|
| `data/suumo_parser_records_raw.csv` | 17,927 | 57 | Raw parser cache with English column names |
| `data/suumo_parser_records_clean.csv` | 17,927 | 132 | Full cleaned history with raw + derived fields |
| `data/suumo_rentals_current.csv` | 17,380 | 132 | Latest record per SUUMO property code |
| `data/suumo_station_access.csv` | 53,044 | 12 | Station-access history, one row per access route |
| `data/suumo_station_access_current.csv` | 51,415 | 12 | Station access for current listings only |

No raw row was deleted. The current dataset is a separate deduplicated view.

## Notebook workflow

- `01_pull_and_cache_overview.ipynb` pulls the source `load_batches` JSON from PostgreSQL/MinIO and writes `data/suumo_parser_records_raw.csv`.
- `02_column_eda.ipynb` loads the raw CSV, profiles each column/value distribution, records field-level cleaning decisions, runs inline sanity checks, creates the clean/current/station CSV files, and writes `data/suumo_clean_report.json`.
- The notebook workflow is intentionally self-contained. The previous helper Python files under `notebook/` were removed so analysis and cleaning are run from `.ipynb` only.

## Data quality result

- `task_id` duplicates: 0.
- Property-code duplicates in history: 547.
- Core missing after parsing: 0.
- Parser failures for rent, fees, area, building age, floors, dates, timestamps, and station access: 0.
- Records requiring rent-per-square-meter review: 3.
- Future-completion/new-build listings: 38; retained as legitimate planned inventory.
- Source columns that are completely empty in this snapshot: Airflow load timestamps/errors and image URL/path fields.

## Hidden missing values

The source uses non-null sentinel text. Important cases include:

- Energy/insulation/utility performance: almost entirely `-`.
- Depreciation and guarantee deposit: almost entirely `-`.
- Deposit: about 90% `-`, interpreted as zero deposit.
- Key money: about 47% `-`, interpreted as zero key money.
- Total units: about 46% unknown.
- Conditions: about 42% unknown.
- Parking: about 39% unavailable.
- Direction: about 11% unknown.

Sentinels are handled per field; they are not globally converted to either zero or null.

## Current-listing distributions

### Numeric summary

| Field | p25 | Median | p75 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Rent (JPY) | 68,000 | 79,000 | 110,000 | 210,000 | 950,000 |
| Management fee (JPY) | 6,500 | 8,000 | 10,000 | 20,000 | 100,000 |
| Exclusive area (m²) | 22.33 | 25.67 | 34.71 | 79.38 | 311.44 |
| Building age (years) | 0 | 7 | 21 | 53 | 99+ |
| Base monthly cost (rent + management) | 75,000 | 87,000 | 119,000 | 229,210 | 995,000 |
| Primary station total travel (minutes) | 5 | 7 | 9 | 16 | 74 |

For bus+walk access, total travel equals bus minutes plus the final walk segment. The station table also retains `mode_minutes` and `final_walk_minutes` separately.

The base monthly cost intentionally excludes parking and unparsed free-form monthly charges.

### Dominant categories

- Layout: `1K` (7,704), `1LDK` (4,666), `1DK` (1,725), `1R` (1,463).
- Building type: mansion/apartment block dominates (`マンション`: 16,533).
- Transaction: intermediary (`仲介`: 17,251).
- Move-in status: immediate 10,461; scheduled 3,837; consultation 3,079.
- Parking information present in the listing: 10,530; source value `-`: 6,850. This does not prove vacancy or bundled parking.

### Geography limitation

All current rows are in Osaka Prefecture, Osaka City, Yodogawa Ward. This sample must not be used to claim conclusions for all Japan without more geographic coverage.

## Derived-column coverage

Fully parsed (100% or effectively 100%):

- Rent, management fee, deposit, key money.
- Exclusive area and building age.
- Building total floors.
- Built/update/next-update dates.
- Primary station and travel minutes except the one source row whose station text is `-`.

Partial by source availability:

- Direction: 89.16%.
- Parking fee: 58.54%.
- Conditions: 58.00%.
- Total units: 53.07%.
- Other initial-cost total: 52.91%.
- Insurance amount: 48.01%.
- Contract type: 44.67%.
- Brokerage fee estimate: 8.62%.

Low coverage reflects source content, not parser failure. Raw text is retained for later rules/NLP.

## Processing decisions

1. Preserve raw text alongside typed columns for auditability.
2. Parse `万円` and `円` values into JPY.
3. Keep brokerage fee in separate JPY/month columns and derive an estimate only when possible.
4. Convert `新築` to age 0; mark `築99年以上` as a lower bound.
5. Parse year-only construction dates with `built_at_precision = year` so January is not mistaken for observed month precision.
6. Parse floor ranges such as `1-3階` into min/max; do not force them into a single floor.
7. Split station access into a one-to-many child table.
8. Keep full history and create a separate latest-per-property current dataset.
9. Flag suspicious values instead of changing or deleting them.
10. Do not display address, phone, remarks, or detailed free text in notebooks/reports.

## Recommended next analytical layer

- Use `suumo_rentals_current.csv` for cross-sectional pricing and supply analysis.
- Use clean history for listing-change and rent-change analysis once more crawl dates accumulate.
- Use `suumo_station_access_current.csv` for station/line accessibility analysis.
- Exclude or manually verify the three rent-per-m² flagged records before model training.
- Add broader geographic crawls before building a Japan-wide model.
- Move the validated typed transformations into dbt staging/intermediate models when notebook rules are accepted.
