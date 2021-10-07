from socsa.light_intensity_jv import argmin_positive
import unittest
from parameterized import parameterized
import pandas as pd
import numpy as np

TEST_CASE_1 = [pd.Series([1, 2, 3, -10, -3, 4, 0.01]), 6]


class Testargmin_positive(unittest.TestCase):
    @parameterized.expand([TEST_CASE_1])
    def test_argmin_positive(self, input, expected):
        out = argmin_positive(input)
        self.assertEqual(out, expected)


if __name__ == "__main__":
    unittest.main()
