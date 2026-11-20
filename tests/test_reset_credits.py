import unittest

from codex_account_manager.reset_credits import parse_reset_balance


class ResetBalanceTests(unittest.TestCase):
    def test_zero_is_a_known_balance(self):
        self.assertEqual(parse_reset_balance({"available_count": 0, "total_earned_count": 3}),
                         {"available": 0, "earned": 3})

    def test_unknown_and_invalid_counts_are_not_zero(self):
        for value in (None, {}, {"available_count": True}, {"available_count": -1},
                      {"available_count": "2"}):
            self.assertIsNone(parse_reset_balance(value))

    def test_available_count_is_authoritative_even_with_partial_credit_details(self):
        self.assertEqual(parse_reset_balance({"available_count": 2, "credits": []}),
                         {"available": 2, "earned": None})
