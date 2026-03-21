import unittest
from oneliner.list_utils import list_reverse


class TestListReverse(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(list_reverse([1, 2, 3]), [3, 2, 1])

    def test_single_element(self):
        self.assertEqual(list_reverse([1]), [1])

    def test_empty(self):
        self.assertEqual(list_reverse([]), [])

    def test_duplicates(self):
        self.assertEqual(list_reverse([1, 1, 2]), [2, 1, 1])


if __name__ == "__main__":
    unittest.main()
