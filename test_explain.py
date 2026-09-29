import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))

from explain import CATEGORIES, build_prompt


class BuildPromptTests(unittest.TestCase):
    def test_includes_all_precomputed_facts(self):
        row = pd.Series({
            "Status": "Amount Mismatch",
            "Category": "Vendor Payment",
            "Amount_GL": -1200.50,
            "Amount_Bank": -1200.00,
            "Amount_Diff": -0.50,
            "Has_Duplicate_ID": False,
            "Description_GL": "Supplier invoice",
            "Description_Bank": "SUPPLIER INVOICE",
        })

        prompt = build_prompt(row)

        self.assertIn("Amount Mismatch", prompt)
        self.assertIn("Vendor Payment", prompt)
        self.assertIn("-1200.50", prompt)
        self.assertIn("-1200.00", prompt)
        self.assertIn("-0.50", prompt)
        self.assertIn("False", prompt)
        self.assertIn("Supplier invoice", prompt)
        self.assertIn("SUPPLIER INVOICE", prompt)
        for category in CATEGORIES:
            self.assertIn(category, prompt)

    def test_handles_missing_bank_side_for_only_in_gl(self):
        row = pd.Series({
            "Status": "Only in GL",
            "Category": "Payroll",
            "Amount_GL": -5000.0,
            "Amount_Bank": float("nan"),
            "Amount_Diff": float("nan"),
            "Has_Duplicate_ID": False,
            "Description_GL": "Monthly salary run",
            "Description_Bank": float("nan"),
        })

        prompt = build_prompt(row)

        self.assertIn("Only in GL", prompt)
        self.assertIn("N/A", prompt)
        self.assertNotIn("nan", prompt.lower())


if __name__ == "__main__":
    unittest.main()
