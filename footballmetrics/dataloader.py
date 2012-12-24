from __future__ import division

import os
import sqlite3

import numpy as np
import pandas as pd
import pandas.io.sql as pd_sql


class DataLoader(object):
    def __init__(self):
        self._df = None

    def load_sqlite(self, db_path, query, index=None):
        '''
        Loads data from a local SQLite database. The database needs
        to be located in *db_path*, *query* is the submitted SQL query.
        '''
        if not os.path.isfile(db_path):
            raise IOError('Database does not exist.')
        con = sqlite3.connect(db_path)
        if index is None:
            self._df = pd_sql.read_frame(query, con)
        else:
            self._df = pd_sql.read_frame(query, con, index_col=index)
        con.close()
        return self._df

    def load_csv(self, filename):
        '''
        Loads the data from a comma-separated values file (CSV).
        The file needs to be located at *filename*.
        '''
        if not os.path.isfile(filename):
            raise IOError('File not found.')
        self._df = pd.read_csv(filename)
        return self._df


class DataHandler(object):
    def __init__(self, games_df=None, standings_df=None):
        if games_df is not None:
            self._games_df = games_df
        if standings_df is not None:
            self._standings_df = standings_df
            if self._standings_df.index.name != 'Team':
                self._standings_df.set_index('Team', inplace=True)
        if games_df is not None and standings_df is not None:
            self._check_integrity()

    def _check_integrity(self):
        '''Checks integrity of the two provided Data Frames.'''
        teams_games = set(self._games_df['HomeTeam']) | set(self._games_df['AwayTeam'])
        teams_standings = set(self.get_teams())
        diff_teams = teams_games - teams_standings
        if diff_teams != set([]):
            raise ValueError('Found differences in available teams.')

    def get_teams(self):
        '''Returns all (unique) teams from Standings Data Frame.'''
        teams = sorted(self._standings_df.index)
        return teams

    def get_wins(self):
        '''Returns the number of wins for each team from Standings Data Frame.'''
        wins = self._standings_df['Win']
        return wins
    
    def get_game_spreads(self, add_to_df=False):
        '''
        Returns the point spread of every game in the Game Data Frame.
        If *add_to_df* is True, the result will be inserted into the Game DF.
        '''
        pt_spreads = self._games_df['HomeScore'] - self._games_df['AwayScore']
        if add_to_df:
            self._games_df['PointSpreads'] = pt_spreads
        return pt_spreads

    def get_mov(self, add_to_df=False):
        '''
        Returns the margin of victory for every team in the Standings Data Frame.
        MoV = (PF - PA) / (# of games).
        If *add_to_df* is True, the result will be inserted into the Standings DF.
        '''
        pt_diff = self._standings_df['PointsFor'] - self._standings_df['PointsAgainst']
        # MoV = Point Differential / (# of games)
        mov = pt_diff / (self._standings_df[['Win', 'Loss', 'Tie']].sum(axis=1))
        if add_to_df:
            self._standings_df['MoV'] = mov
        return mov

    def get_scoring_over_avg(self, key='offense'):
        '''
        Returns the scoring of a team's offense/defense over average.
        Sc_off = (PF / (# of games)) - Avg(PF / (# of games))
        *key* controls, whether scoring for offense or defense is calculated.
        key = {'offense', 'defense'}
        '''
        n_games = self._standings_df[['Win', 'Loss', 'Tie']].sum(axis=1)
        if key == 'offense':
            score = self._standings_df['PointsFor'] / n_games
        elif key == 'defense':
            score = self._standings_df['PointsAgainst'] / n_games
        else:
            raise ValueError("key must be in ['offense', 'defense'].")
        score -= score.mean()
        return score
