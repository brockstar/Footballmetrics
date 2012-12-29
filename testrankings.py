import unittest

import pandas as pd

import footballmetrics.dataloader as fm_dl
import footballmetrics.rankings as fm_rkg


class TestRankings(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test.db'
        self.games_df = fm_dl.from_sqlite('test.db', 'select * from games')
        self.standings_df = fm_dl.from_sqlite('test.db', 'select * from standings')

    def test_fisb_rating(self):
        fisb = fm_rkg.FISB_Ranking(self.games_df)
        ratings = dict(fisb.calculate_ranking())
        result = {'A': 1.85, 'B': -3.35, 'C': -3.65, 'D': 5.15, 'Home field advantage': -1.4}
        for k in result:
            self.assertAlmostEqual(ratings[k], result[k], places=1)

    def test_fisb_bootstrap(self):
        fisb = fm_rkg.FISB_Ranking(self.games_df)
        ratings = dict(fisb.calculate_ranking(10000))
        result = {'A': 2.44, 'B': -4.40, 'C': -5.35, 'D': 7.32, 'Home field advantage': -0.25}
        for k in ratings:
            self.assertAlmostEqual(ratings[k], result[k], places=0)

    def test_fisb_calculate_argument_type(self):
        fisb = fm_rkg.FISB_Ranking(self.games_df)
        self.assertRaises(TypeError, fisb.calculate_ranking, 'no_number', nprocs=2)
        self.assertRaises(TypeError, fisb.calculate_ranking, 1000, nprocs='no number')

    def test_fisb_normalize(self):
        fisb = fm_rkg.FISB_Ranking(self.games_df)
        # average of testratings is 1.066
        testratings = pd.Series({'A': 3.5, 'B': -1.2, 'C': 0.9})
        self.assertAlmostEqual(0, fisb._normalize(testratings).mean(), places=5)

    def test_ml_rating(self):
        ml = fm_rkg.ML_Ranking(self.games_df, self.standings_df)
        ratings = ml.calculate_ranking()
        result = {'A': 0.70, 'B': 0.70, 'C': 1.37, 'D': 1.37}
        for k in result:
            self.assertAlmostEqual(ratings[k], result[k], places=1)

    def test_srs_rating(self):
        s = fm_rkg.SRS(self.games_df, self.standings_df)
        srs, mov, sos = s.calculate_ranking()
        srs_opt = {'A': 1.5, 'B': -3.0, 'C': -4.0, 'D': 5.5}
        mov_opt = {'A': 2.0, 'B': -4.0, 'C': -5.3, 'D': 7.3}
        sos_opt = {'A': -0.5, 'B': 1.0, 'C': 1.3, 'D': -1.8}
        for k in srs:
            self.assertAlmostEqual(srs[k], srs_opt[k], places=1)
            self.assertAlmostEqual(mov[k], mov_opt[k], places=1)
            self.assertAlmostEqual(sos[k], sos_opt[k], places=1)

    def test_srs_rating_offense(self):
        s = fm_rkg.SRS(self.games_df, self.standings_df)
        srs, mov, sos = s.calculate_ranking(method='offense')
        srs_opt = {'A': 0.25, 'B': -3.25, 'C': -7.25, 'D': 10.25}
        mov_opt = {'A': 0.3, 'B': -4.3, 'C': -9.7, 'D': 13.7}
        sos_opt = {'A': -0.1, 'B': 1.1, 'C': 2.4, 'D': -3.4}
        for k in srs:
            self.assertAlmostEqual(srs[k], srs_opt[k], places=1)
            self.assertAlmostEqual(mov[k], mov_opt[k], places=1)
            self.assertAlmostEqual(sos[k], sos_opt[k], places=1)

    def test_srs_rating_defense(self):
        s = fm_rkg.SRS(self.games_df, self.standings_df)
        srs, mov, sos = s.calculate_ranking(method='defense')
        srs_opt = {'A': -1.25, 'B': -0.25, 'C': -3.25, 'D': 4.75}
        mov_opt = {'A': -1.7, 'B': -0.3, 'C': -4.3, 'D': 6.3}
        sos_opt = {'A': 0.4, 'B': 0.1, 'C': 1.1, 'D': -1.6}
        for k in srs:
            self.assertAlmostEqual(srs[k], srs_opt[k], places=1)
            self.assertAlmostEqual(mov[k], mov_opt[k], places=1)
            self.assertAlmostEqual(sos[k], sos_opt[k], places=1)

    def test_srs_invalid_method(self):
        s = fm_rkg.SRS(self.games_df, self.standings_df)
        self.assertRaises(ValueError, s.calculate_ranking, 'invalid_method')


if __name__ == '__main__':
    unittest.main()
