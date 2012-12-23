from __future__ import division

import sqlite3
import unittest

import pandas as pd
import footballmetrics.dataloader as fm_dl


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        gamesdict = {'HomeTeam': ['A', 'C', 'B', 'A', 'C', 'D'],
                     'AwayTeam': ['B', 'D', 'D', 'C', 'B', 'A'],
                     'HomeScore': [27, 17, 31, 3, 14, 42],
                     'AwayScore': [13, 41, 28, 10, 13, 41]}
        self.games = pd.DataFrame(gamesdict)
    
    def test_load_sqlite(self):
        dl = fm_dl.DataLoader()
        df = dl.load_sqlite('test.db', 'select * from games')
        for key in df:
            series = df[key] == self.games[key]
            self.assert_(list(series.unique()) == [True])

    def test_load_sqlite_nodb(self):
        dl = fm_dl.DataLoader()
        self.assertRaises(IOError, dl.load_sqlite, 'nodb.db', 'select * from games')

    def test_load_sqlite_invalid_query(self):
        dl = fm_dl.DataLoader()
        self.assertRaises(sqlite3.OperationalError, dl.load_sqlite, 'test.db', 'select * from invalid_table')


if __name__ == '__main__':
    unittest.main()
