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

    def test_load_csv(self):
        dl = fm_dl.DataLoader()
        df = dl.load_csv('test_dataloader.csv')
        for key in df:
            series = df[key] == self.games[key]
            self.assert_(list(series.unique()) == [True])

    def test_load_csv_nofile(self):
        dl = fm_dl.DataLoader()
        self.assertRaises(IOError, dl.load_csv, 'nofile.csv')


class TestDataHandler(unittest.TestCase):
    def setUp(self):
        dl = fm_dl.DataLoader()
        self.games = dl.load_sqlite('test.db', 'select * from games')
        self.standings = dl.load_sqlite('test.db', 'select * from standings', index='Team')
        self.dh = fm_dl.DataHandler(self.games, self.standings)
   
    def test_get_teams(self):
        self.assertEqual(self.dh.get_teams(), ['A', 'B', 'C', 'D'])

    def test_get_game_spreads(self):
        margins = self.games['HomeScore'] - self.games['AwayScore']
        series = self.dh.get_game_spreads() == margins
        self.assert_(list(series.unique()) == [True])

    def test_get_wins(self):
        wins = self.standings['Win']
        series = wins == self.dh.get_wins()
        self.assertEqual(list(series.unique()), [True])

    def test_no_df_set(self):
        dh = fm_dl.DataHandler()
        self.assertRaises(AttributeError, dh.get_wins)
        self.assertRaises(AttributeError, dh.get_teams)
        self.assertRaises(AttributeError, dh.get_game_spreads)


if __name__ == '__main__':
    unittest.main()
