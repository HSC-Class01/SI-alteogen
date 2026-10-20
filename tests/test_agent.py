import unittest

from agent import analyze, normalize, number, ratio


class FinancialParsingTests(unittest.TestCase):
    def test_number_handles_commas_and_parentheses(self):
        self.assertEqual(number("1,234"), 1234)
        self.assertEqual(number("(250)"), -250)
        self.assertIsNone(number("-"))

    def test_ratio_rejects_missing_and_nonpositive_denominators(self):
        self.assertIsNone(ratio(10, 0))
        self.assertIsNone(ratio(10, -2, positive=True))
        self.assertEqual(ratio(25, 100), 25.0)

    def test_ambiguous_accounts_are_not_selected(self):
        rows = [
            {"sj_div": "IS", "account_id": "ifrs-full_Revenue", "account_nm": "매출액",
             "currency": "KRW", "thstrm_amount": "100"},
            {"sj_div": "IS", "account_id": "ifrs-full_Revenue", "account_nm": "매출액",
             "currency": "KRW", "thstrm_amount": "120"},
        ]
        metrics = {"revenue": {"statements": ["IS"], "ids": ["ifrs-full_Revenue"],
                               "names": ["매출액"], "type": "income"}}
        record = normalize(rows, 2025, "11011", "CFS", metrics)
        self.assertIsNone(record["values"]["revenue"])
        self.assertIn("ambiguous account mapping", record["issues"][0])

    def test_analyze_calculates_period_margins(self):
        record = {
            "year": 2025, "code": "11011", "basis": "CFS",
            "values": {"revenue": 200, "operating_profit": 20, "net_income": 10,
                       "liabilities": 50, "equity": 100, "current_assets": 40,
                       "current_liabilities": 20, "assets": 150},
            "issues": [],
        }
        result = analyze([record])[0]
        self.assertEqual(result["ratios"]["operating_margin"], 10.0)
        self.assertEqual(result["ratios"]["current_ratio"], 200.0)


if __name__ == "__main__":
    unittest.main()
