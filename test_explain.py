import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))

from explain import CATEGORIES, build_prompt, explain_row


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


class ExplainRowTests(unittest.TestCase):
    def test_returns_model_answer_and_uses_given_model(self):
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

        fake_response = {
            "message": {
                "content": "Category: timing difference\nExplanation: Small rounding gap.",
            }
        }

        with patch("explain.ollama.chat", return_value=fake_response) as mock_chat:
            answer = explain_row(row, model="qwen2.5:7b")

        self.assertEqual(answer, fake_response["message"]["content"])
        mock_chat.assert_called_once()
        _, kwargs = mock_chat.call_args
        self.assertEqual(kwargs["model"], "qwen2.5:7b")
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertIn("Amount Mismatch", kwargs["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
