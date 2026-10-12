# Financial Report Generator

![CI](https://github.com/Lukegbb/financial-report-generator/actions/workflows/ci.yml/badge.svg)

A small command-line tool that reads a CSV of income and expenses and produces:

- a text report with total income, expenses, balance and **savings rate**
- a **month-by-month** breakdown
- **spending by category**
- two charts saved as PNG (income vs expenses per month, and a category pie chart)

The CSV is validated first, so a missing column, an unknown transaction type or a bad date gives a clear error instead of a stack trace.

## Usage

```bash
pip install -r requirements.txt
python finance_report.py transactions.csv --output reports/
```

Options:

| Option | Description |
|---|---|
| `csv` | Path to the CSV file (default: `transactions.csv`) |
| `-o, --output` | Folder for `report.txt` and the charts (default: `reports/`) |
| `--no-charts` | Only generate the text report |

### Example output

```
FINANCIAL REPORT
================
Total income:   €36,200.00
Total expenses: €10,890.00
Balance:        €25,310.00
Savings rate:   69.9%

By month
--------
2024-01  income €  8,500.00   expenses €  2,000.00   balance €  6,500.00
...
```

## CSV format

| Column | Example | Notes |
|---|---|---|
| `date` | `2024-01-05` | YYYY-MM-DD |
| `description` | `Rent` | free text |
| `category` | `Housing` | used for the category breakdown |
| `type` | `income` / `expense` | |
| `amount` | `1200.00` | positive or negative, both work |

A sample file with four months of data is included (`transactions.csv`).

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

The tests cover the totals, the monthly and category breakdowns, CSV validation and the command-line run. They run on every push with GitHub Actions.

## Tech

Python 3, pandas, matplotlib, argparse, unittest.
