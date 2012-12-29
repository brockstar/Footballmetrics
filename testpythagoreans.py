from __future__ import division

import unittest

import numpy as np

import footballmetrics.dataloader as fm_dl
import footballmetrics.pythagoreans as fm_pyth


class TestPythagoreans(unittest.TestCase):
    def setUp(self):
        self._df = fm_dl.DataLoader().load_sqlite('test.db', 'select * from standings')
        self.Pythagorean = fm_pyth.PythagoreanExpectation(self._df)

    def test_pythagorean_exp_calculator(self):
        pyth = fm_pyth.get_pythag 
        self.assertAlmostEqual(pyth(100, 75), 0.68, places=2)
        self.assertAlmostEqual(pyth(100, 75, 5.0), 0.81, places=2)
        self.assertEqual(pyth(100, 0), 1.0)
        self.assertRaises(ZeroDivisionError, pyth, 0, 0)

    def test_pyth_exp_no_opt(self):
        pyth = self.Pythagorean.calculate_pythagorean(optimize=False)
        result = {'A': 0.56, 'B': 0.38, 'C': 0.30, 'D': 0.64}
        for key in result:
            self.assertAlmostEqual(pyth[key], result[key], places=2)

    def test_pyth_set_exp(self):
        val = 3.0
        result = np.array([3.0])
        self.Pythagorean.set_exponent(val)
        self.assertEqual(self.Pythagorean.get_exponent(), result)
        values = [3.0, 6.4]
        result = np.array(values)
        self.Pythagorean.set_exponent(values)
        exponent = self.Pythagorean.get_exponent()
        for i in range(len(result)):
            self.assertEqual(exponent[i], result[i])


if __name__ == '__main__':
    unittest.main()
