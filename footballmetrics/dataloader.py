from __future__ import division

import os
import sqlite3

import pandas as pd
import pandas.io.sql as pd_sql


def from_sqlite(db_path, query, index=None):
    '''
    Loads data from a local SQLite database.
    
    Parameters
    ----------
    db_path : string
        Path to SQLite database.
    query : string
        Query sent to database.

    Returns
    -------
    df : pandas DataFrame
        This object is a DataFrame representation of the SQLite data.
    '''
    if not os.path.isfile(db_path):
        raise IOError('Database does not exist.')
    con = sqlite3.connect(db_path)
    if index is None:
        df = pd_sql.read_frame(query, con)
    else:
        df = pd_sql.read_frame(query, con, index_col=index)
    con.close()
    return df

def from_csv(filename, index=None):
    '''
    Loads data from a comma-separated values file (CSV).
    
    Parameters
    ----------
    filename : string
        Path to CSV file.
    index : string
        Name of column that shall be set as index.

    Returns
    -------
    df : pandas DataFrame
        This object is a DataFrame representation of the CSV data.
    '''
    if not os.path.isfile(filename):
        raise IOError('File not found.')
    if index is None:
        df = pd.read_csv(filename)
    else:
        df = pd.read_csv(filename, index_col=index)
    return df


class DataHandler(object):
    def __init__(self, games_df=None, standings_df=None):
        '''
        A class that is capable of performing various tasks on football data.
        There are methods that apply to game data and others that apply
        to standings. It's not necessary that both are set.

        Parameters
        ----------
        games_df : pandas DataFrame
            DataFrame containing game data. Following columns are expected:
            [HomeTeam, AwayTeam, HomeScore, AwayScore]
        standings_df : pandas DataFrame
            DataFrame containing standings. Following columns are expected:
            [Win, Loss, Tie, PointsFor, PointsAgainst]

        Notes
        -----
        Depending on the tasks to be performed it may be sufficient, if
        games_df/standings_df only contains a subset of the expected keys.
        For example PointsFor/PointsAgainst isn't needed for returning 
        the unique teams contained in the DataFrame.
        
        Nevertheless, if all expected keys are set, all available methods
        can be used.
        '''
        if type(games_df) == pd.core.frame.DataFrame:
            self._games_df = games_df
        elif games_df is None:
            self._games_df = None
        else:
            raise TypeError('games_df not None or pandas DataFrame.')
        if type(standings_df) == pd.core.frame.DataFrame:
            self._standings_df = standings_df
            if self._standings_df.index.name != 'Team':
                self._standings_df.set_index('Team', inplace=True)
        elif standings_df is None:
            self._standings_df = None
        else:
            raise TypeError('standings_df not None or pandas DataFrame.')
        if self._games_df is not None and self._standings_df is not None:
            # Needs to be implemented!
            self._check_integrity()
            #pass

    def _check_integrity(self):
        '''Checks integrity of the two provided Data Frames.'''
        teams_games = set(self._games_df['HomeTeam']) | set(self._games_df['AwayTeam'])
        teams_standings = set(self.get_teams())
        diff_teams = teams_games - teams_standings
        if diff_teams != set([]):
            raise ValueError('Found differences in available teams.')

    def get_teams(self):
        '''
        Get all (unique) teams.
        
        Returns
        -------
        teams : pandas Series
            Series contains all found teams.

        Notes
        -----
        Works with either standings_df or games_df.
        '''
        if self._standings_df is None and self._games_df is None:
            raise AttributeError('games_df and standings_df not set.')
        elif self._games_df is None:
            teams = sorted(self._standings_df.index)
        else:
            teams = sorted(set(self._games_df['HomeTeam']) | set(self._games_df['AwayTeam']))
        return teams

    def get_opponents(self):
        '''
        Get opponents of all teams in games_df.
        
        Returns
        -------
        opponents : pandas Series
            Contains opponents for all teams.
        '''
        if self._games_df is None:
            raise AttributeError('games_df not set.')
        else:
            games = self.get_games()
            def get_opp(team):
                opp = list(games[games['HomeTeam'] == team]['AwayTeam'])
                opp += list(games[games['AwayTeam'] == team]['HomeTeam'])
                return opp
            opponents = pd.DataFrame({team: get_opp(team) for team in self.get_teams()})
            return opponents       

    def get_wins(self):
        '''
        Get number of wins for each team from standings_df.
        
        Returns
        -------
        wins : pandas Series
            Contains number of wins for each team.
        '''
        if self._standings_df is None:
            raise AttributeError('standings_df not set.')
        else:
            wins = self._standings_df['Win']
            return wins

    def get_number_of_games(self):
        '''
        Get number of games for each team in standings_df.
        
        Returns
        -------
        n_games : pandas Series
            Contains number of games each team has played.
        '''
        if self._standings_df is None:
            raise ValueError('standings_df not set.')
        else:
            n_games = self._standings_df[['Win', 'Loss', 'Tie']].sum(axis=1)
            return n_games

    def get_games(self):
        '''
        Get all games.
        
        Returns
        -------
        games : pandas DataFrame
            Returns the data set in games_df.
        '''
        if self._games_df is None:
            raise AttributeError('games_df not set.')
        else:
            return self._games_df

    def get_game_spreads(self, add_to_df=False):
        '''
        Get point spread of every game in games_df.

        Parameters
        ----------
        add_to_df : bool
            If True point spreads will be inserted into games_df.

        Returns
        -------
        spreads : pandas Series
            Contains point spread of every single game.
        '''
        if self._games_df is None:
            raise AttributeError('games_df not set.')
        else:
            pt_spreads = self._games_df['HomeScore'] - self._games_df['AwayScore']
            if add_to_df:
                self._games_df['PointSpreads'] = pt_spreads
            return pt_spreads

    def get_mov(self, add_to_df=False):
        '''
        Get margin of victory for every team in standings_df.
        MoV = (PF - PA) / (# of games).

        Parameters
        ----------
        add_to_df : bool
            If True MoV's will be inserted into standings_df.

        Returns
        -------
        mov : pandas Series
            Contains the margin of victory for every team.
        '''
        if self._standings_df is None:
            raise AttributeError('standings_df not set.')
        else:
            pt_diff = self._standings_df['PointsFor'] - self._standings_df['PointsAgainst']
            # MoV = Point Differential / (# of games)
            mov = pt_diff / self.get_number_of_games()
            if add_to_df:
                self._standings_df['MoV'] = mov
            return mov

    def get_scoring_over_avg(self, key='offense', add_to_df=False):
        '''
        Get scoring of a team's offense/defense over average.
        For offense scoring over average is defined as:
            Sc_off = (PF / (# of games)) - Avg(PF / (# of games))
        
        Parameters
        ----------
        key : {'offense', 'defense'}
            Decides, whether offensive or defensive scoring over average
            is calculated.
        add_to_df : bool
            If True scoring over average will be inserted into standings_df.
        
        Returns
        -------
        score : pandas Series
            Contains scoring over average for every team.
        '''
        if self._standings_df is None:
            raise AttributeError('standings_df not set.')
        else:
            n_games = self.get_number_of_games()
            if key == 'offense':
                score = self._standings_df['PointsFor'] / n_games
            elif key == 'defense':
                score = self._standings_df['PointsAgainst'] / n_games
            else:
                raise ValueError("key must be in ['offense', 'defense'].")
            score -= score.mean()
            if add_to_df:
                col_name = key + '_scoring'
                self._standings_df[col_name] = score
            return score
