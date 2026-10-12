"""Generate a financial report (text + charts) from a CSV of transactions.

Usage:
    python finance_report.py transactions.csv --output reports/
"""
import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"date", "description", "category", "type", "amount"}


class InvalidDataError(ValueError):
    """Raised when the CSV doesn't have the expected format."""


def load_transactions(path):
    """Read and validate the CSV. Amounts are always stored as positive numbers."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise InvalidDataError(f"Missing columns: {', '.join(sorted(missing))}")

    df["type"] = df["type"].str.strip().str.lower()
    bad_types = set(df["type"]) - {"income", "expense"}
    if bad_types:
        raise InvalidDataError(f"Unknown transaction type(s): {', '.join(sorted(bad_types))}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise InvalidDataError("Some rows have an invalid date (expected YYYY-MM-DD).")

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").abs()
    if df["amount"].isna().any():
        raise InvalidDataError("Some rows have an invalid amount.")

    return df.sort_values("date").reset_index(drop=True)


def summarise(df):
    """Return overall totals, a month-by-month table and spending per category."""
    income = df.loc[df["type"] == "income", "amount"].sum()
    expenses = df.loc[df["type"] == "expense", "amount"].sum()

    monthly = (
        df.assign(month=df["date"].dt.to_period("M").astype(str))
        .pivot_table(index="month", columns="type", values="amount", aggfunc="sum", fill_value=0)
        .reindex(columns=["income", "expense"], fill_value=0)
    )
    monthly["balance"] = monthly["income"] - monthly["expense"]

    by_category = (
        df[df["type"] == "expense"].groupby("category")["amount"].sum().sort_values(ascending=False)
    )

    return {
        "income": round(float(income), 2),
        "expenses": round(float(expenses), 2),
        "balance": round(float(income - expenses), 2),
        "savings_rate": round(float((income - expenses) / income * 100), 1) if income else 0.0,
        "monthly": monthly,
        "by_category": by_category,
    }


def format_report(summary, currency="€"):
    lines = [
        "FINANCIAL REPORT",
        "================",
        f"Total income:   {currency}{summary['income']:,.2f}",
        f"Total expenses: {currency}{summary['expenses']:,.2f}",
        f"Balance:        {currency}{summary['balance']:,.2f}",
        f"Savings rate:   {summary['savings_rate']}%",
        "",
        "By month",
        "--------",
    ]
    for month, row in summary["monthly"].iterrows():
        lines.append(
            f"{month}  income {currency}{row['income']:>10,.2f}   "
            f"expenses {currency}{row['expense']:>10,.2f}   balance {currency}{row['balance']:>10,.2f}"
        )
    lines += ["", "Spending by category", "--------------------"]
    for category, total in summary["by_category"].items():
        lines.append(f"{category:<15}{currency}{total:>10,.2f}")
    return "\n".join(lines) + "\n"


def save_charts(summary, output_dir):
    """Save a monthly income-vs-expenses chart and a category pie chart as PNG files."""
    import matplotlib

    matplotlib.use("Agg")  # no window needed, works on servers/CI
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)

    ax = summary["monthly"][["income", "expense"]].plot(kind="bar", color=["#16a34a", "#dc2626"], figsize=(8, 4))
    ax.set_title("Income vs expenses per month")
    ax.set_xlabel("")
    ax.set_ylabel("Amount")
    plt.tight_layout()
    monthly_path = output_dir / "monthly.png"
    plt.savefig(monthly_path)
    plt.close()

    summary["by_category"].plot(kind="pie", autopct="%1.0f%%", figsize=(5, 5), ylabel="")
    plt.title("Spending by category")
    plt.tight_layout()
    category_path = output_dir / "categories.png"
    plt.savefig(category_path)
    plt.close()

    return [monthly_path, category_path]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a financial report from a CSV file.")
    parser.add_argument("csv", nargs="?", default="transactions.csv", help="path to the transactions CSV")
    parser.add_argument("-o", "--output", default="reports", help="folder for the report and charts")
    parser.add_argument("--no-charts", action="store_true", help="only generate the text report")
    args = parser.parse_args(argv)

    try:
        df = load_transactions(args.csv)
    except FileNotFoundError:
        parser.error(f"file not found: {args.csv}")
    except InvalidDataError as exc:
        parser.error(str(exc))

    summary = summarise(df)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    report = format_report(summary)
    (output / "report.txt").write_text(report, encoding="utf-8")
    print(report)

    if not args.no_charts:
        for path in save_charts(summary, output):
            print(f"Chart saved to {path}")


if __name__ == "__main__":
    main()
