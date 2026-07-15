# Data guide

GateSignal projects can be stored as `.xlsx` or `.json`. Download the template from the sidebar to preserve the expected names. Workbook sheets are case-insensitive and spaces are converted to underscores.

## Metadata

The `Metadata` sheet uses `field` and `value` columns. Recognized app fields are:

| Field | Meaning |
|---|---|
| `project_name` | Human-readable concept name |
| `decision_question` | The specific investment question |
| `decision_owner` | Accountable person or group |
| `review_stage` | Context label, not a proprietary stage definition |
| `currency` | Display label only |
| `discount_rate` | Decimal from 0 to 1 |

## Criteria

| Column | Type and boundary |
|---|---|
| `category` | Short grouping label |
| `criterion` | Unique, specific criterion |
| `weight` | Positive number; normalized during analysis |
| `score` | 0–10 preference score |
| `evidence_strength` | Ordinal 0–3 |
| `must_pass` | Yes/no or true/false |
| `threshold` | 0–10; used only for a must-pass row |
| `evidence_note` | Source and limitation note |

## Cash flows

The `Cash flows` sheet is long-form: one row per scenario and period.

| Column | Type and boundary |
|---|---|
| `scenario` | Scenario name |
| `probability` | Decimal 0–1, constant within a scenario; unique scenarios sum to 1 |
| `period` | Whole number starting at 0 |
| `cash_flow` | Signed forward cash flow |

Missing periods are treated as zero. Period zero should contain only relevant future commitments and releases; sunk spending belongs in the narrative, not in forward economics.

## Volume bridge

Each scenario is unique. `market_size`, `additional_units_per_repeater`, and `unit_contribution` must be non-negative. The four rate columns—`awareness_rate`, `availability_rate`, `trial_rate`, and `repeat_rate`—are decimals from 0 to 1.

## Risks

| Column | Type and boundary |
|---|---|
| `risk` | Unique uncertainty statement |
| `owner` | Person responsible for monitoring and action |
| `probability` | Ordinal 1–5 |
| `impact` | Ordinal 1–5 |
| `evidence_strength` | Ordinal 0–3 |
| `mitigation` | Action taken before the risk materializes |
| `trigger` | Observable condition for escalation or response |
| `response` | Action if the trigger occurs |

## Challenge

`check` must be unique, `completed` accepts yes/no or true/false, and `note` records the challenge evidence. Teams may adapt the checklist to their governance context.

## Safety limits

GateSignal accepts only `.xlsx` and `.json`; it does not execute macros or embedded code. Uploads default to a 50 MB limit, workbooks may not expand beyond 100 MB, and each analytical table is limited to 20,000 rows. Spreadsheet exports neutralize text beginning with `=`, `+`, `-`, or `@` to reduce formula-injection risk.

