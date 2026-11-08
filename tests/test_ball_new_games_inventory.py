import unittest
from tools.ball_new_games_inventory import selected_indices


class InventoryTests(unittest.TestCase):
    def test_selection_bounded_for_small_and_full_archives(self):
        self.assertEqual(selected_indices(1),[0])
        self.assertEqual(selected_indices(57),[0,19,38,56])
        for n in range(1,80):
            selected=selected_indices(n)
            self.assertEqual(selected,sorted(set(selected)))
            self.assertTrue(all(0<=i<n for i in selected))
        with self.assertRaises(ValueError):selected_indices(0)
