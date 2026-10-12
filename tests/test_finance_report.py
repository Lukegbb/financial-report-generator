import tempfile
import unittest
from pathlib import Path

from finance_report import InvalidDataError, format_report, load_transactions, main, summarise

SAMPLE = """date,description,category,type,amount
2024-01-05,Salary,Salary,income,3000
2024-01-10,Rent,Housing,expense,1200
2024-01-12,Groceries,Food,expense,-300
2024-02-01,Salary,Salary,income,3000
2024-02-05,Rent,Housing,expense,1200
"""


class FinanceReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.csv = self.dir / "transactions.csv"
        self.csv.write_text(SAMPLE)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, content):
        path = self.dir / "custom.csv"
        path.write_text(content)
        return path

    def test_totals_and_savings_rate(self):
        summary = summarise(load_transactions(self.csv))
        self.assertEqual(summary["income"], 6000)
        self.assertEqual(summary["expenses"], 2700)  # negative amounts are normalised
        self.assertEqual(summary["balance"], 3300)
        self.assertEqual(summary["savings_rate"], 55.0)

    def test_monthly_breakdown(self):
        monthly = summarise(load_transactions(self.csv))["monthly"]
        self.assertEqual(list(monthly.index), ["2024-01", "2024-02"])
        self.assertEqual(monthly.loc["2024-01", "balance"], 1500)

    def test_spending_by_category_is_sorted(self):
        by_category = summarise(load_transactions(self.csv))["by_category"]
        self.assertEqual(list(by_category.index), ["Housing", "Food"])

    def test_missing_columns_raise_error(self):
        path = self.write("date,amount\n2024-01-01,10\n")
        with self.assertRaises(InvalidDataError):
            load_transactions(path)

    def test_unknown_type_raises_error(self):
        path = self.write("date,description,category,type,amount\n2024-01-01,X,Y,refund,10\n")
        with self.assertRaises(InvalidDataError):
            load_transactions(path)

    def test_invalid_date_raises_error(self):
        path = self.write("date,description,category,type,amount\nyesterday,X,Y,income,10\n")
        with self.assertRaises(InvalidDataError):
            load_transactions(path)

    def test_report_text(self):
        report = format_report(summarise(load_transactions(self.csv)))
        self.assertIn("Balance:        €3,300.00", report)
        self.assertIn("Housing", report)

    def test_cli_writes_report_and_charts(self):
        out = self.dir / "out"
        main([str(self.csv), "--output", str(out)])
        self.assertTrue((out / "report.txt").exists())
        self.assertTrue((out / "monthly.png").exists())
        self.assertTrue((out / "categories.png").exists())


if __name__ == "__main__":
    unittest.main()
