import unittest

import footballmetrics.dataloader as fm_dl
import footballmetrics.sos as fm_sos


class TestSOS(unittest.TestCase):
    def setUp(self):
        games = fm_dl.from_sqlite('test.db', 'select * from games')
        standings = fm_dl.from_sqlite('test.db', 'select * from standings')
        self.sos_obj = fm_sos.SOS(games, standings)

    def test_average(self):
        ratings = {'A': 1.85, 'B': -3.35, 'C': -3.65, 'D': 5.15}
        sos = self.sos_obj.calculate(method='average', ratings=ratings)
        sos = {team: round(sos[team], 2) for team in sos.index}
        expected = {'A': -0.62, 'B': 1.12, 'C': 1.22, 'D': -1.72}
        self.assertDictEqual(sos, expected)

    def test_scaled_average(self):
        ratings = {'A': 1.85, 'B': -3.35, 'C': -3.65, 'D': 5.15}
        sos = self.sos_obj.calculate(method='scaled', ratings=ratings)
        sos = {team: round(sos[team], 2) for team in sos.index}
        expected = {'A': 0.34, 'B': 0.54, 'C': 0.55, 'D': 0.22}
        self.assertDictEqual(sos, expected)

    def test_bcs(self):
        sos = self.sos_obj.calculate(method='bcs')
        sos = {team: round(sos[team], 2) for team in sos.index}
        expected = {'A': 0.53, 'B': 0.53, 'C': 0.47, 'D': 0.47}
        self.assertDictEqual(sos, expected)

    def test_no_ratings_set(self):
        self.assertRaises(ValueError, self.sos_obj.calculate, 'average', None)
        self.assertRaises(ValueError, self.sos_obj.calculate, 'scaled', None)


if __name__ == '__main__':
    unittest.main()
