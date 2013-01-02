from __future__ import division

import numpy as np
import pandas as pd

import footballmetrics.dataloader as fm_dl
import footballmetrics.rankings as fm_rkg
import footballmetrics.pythagoreans as fm_pyth


class Metrics(object):
    def __init__(self, games_df, standings_df, autocalc=True):
        '''
        This class is intented to be a centerpiece of the
        footballmetrics module. Rankings and pythagoreans can be accessed
        easily, without knowing the internals of the respective modules.
        It is kind of a superclass accessing all the low-level modules.

        Parameters
        ----------
        games_df : pandas DataFrame
            Contains game data for every game played.
        standings_df : pandas DataFrame
            Contains standings for every team.
        autocalc : bool
            If set True, rankings will be calculated automatically
            when accessed and not previously calculated.

        Methods
        -------
        calc_ranking(method='fisb')
        calc_pythag(method='pyth')

        Attributes
        ----------
        fisb : pandas Series
            FISB ranking
        ml : pandas Series
            Max-L ranking
        srs : pandas DataFrame
            Simple Ranking System. Returns SRS, MoV and SoS
        pythagorean : pandas Series
            Pythagorean Expectation
        pythagenport : pandas Series
            Pythagenport
        pythagenpat : pandas Series
            Pythagenpat
        '''
        self._games_df = games_df
        self._standings_df = standings_df
        self._autocalc = autocalc
        self._dh = fm_dl.DataHandler(games_df=games_df,
                                     standings_df=standings_df)
        self._initialize_stats_df()

    # =============
    # Data handling
    # =============

    def _initialize_stats_df(self):
        nteams = len(self._dh.get_teams())
        teams = list(self._dh.get_teams())
        teams.append('Home field advantage')
        nan = np.empty((nteams + 1, ))
        nan.fill(np.nan)
        stat_names = ['FISB', 'Max-L', 'SRS', 'MOV', 'SOS',
                      'Pythagorean', 'Pythagenport', 'Pythagenpat']
        self._is_calced = {stat: False for stat in stat_names}
        df_dict = {stat: nan for stat in stat_names}
        self._stats = pd.DataFrame(df_dict, index=sorted(teams))

    def reset(self):
        '''
        Resets calculated results, but not input data.
        '''
        self._initialize_stats_df()

    # =========================
    # Rankings and Pythagoreans
    # =========================

    def calc_ranking(self, method='fisb'):
        '''
        Calculates specified ranking.

        Parameters
        ----------
        method : {'fisb', 'ml', 'srs'}
            Defines the ranking system that will be calculated.
        '''
        if method == 'fisb':
            _fisb = fm_rkg.FISB_Ranking(self._games_df)
            self._stats['FISB'] = _fisb.calculate_ranking()
            self._is_calced['FISB'] = True
        elif method == 'ml':
            _ml = fm_rkg.ML_Ranking(games_df=self._games_df,
                                    standings_df=self._standings_df)
            self._stats['Max-L'] = _ml.calculate_ranking()
            self._is_calced['Max-L'] = True
        elif method == 'srs':
            _s = fm_rkg.SRS(games_df=self._games_df,
                            standings_df=self._standings_df)
            _srs, _mov, _sos = _s.calculate_ranking()
            _df = pd.DataFrame({'SRS': _srs, 'MOV': _mov, 'SOS': _sos})
            self._stats[['SRS', 'MOV', 'SOS']] = _df
            self._is_calced['SRS'] = True
        else:
            raise ValueError('Method "{0}" not found. \
                Must be in {{"fisb", "ml", "srs"}}.'.format(method))

    def calc_pythag(self, method='pyth'):
        '''
        Calculates pythagorean expectation with specified method.

        Parameters
        ----------
        method : {'pyth', 'port', 'pat'}
            Determines if classic Pythagorean Expectation (pyth), Pythagenport
            (port) or Pythagenpat (pat) is calculated.

        Notes
        -----
        For further details see:
        http://bit.ly/xhBxiD (directs to footballissexbaby.de)
        '''
        if method == 'pyth':
            _pyth = fm_pyth.PythagoreanExpectation(self._standings_df)
            self._stats['Pythagorean'] = _pyth.calculate_pythagorean()
            self._is_calced['Pythagorean'] = True
        elif method == 'port':
            _pyth = fm_pyth.Pythagenport(self._standings_df)
            self._stats['Pythagenport'] = _pyth.calculate_pythagorean()
            self._is_calced['Pythagenport'] = True
        elif method == 'pat':
            _pyth = fm_pyth.Pythagenpat(self._standings_df)
            self._stats['Pythagenpat'] = _pyth.calculate_pythagorean()
            self._is_calced['Pythagenpat'] = True
        else:
            raise ValueError('Method "{0}" not found. \
                Must be in {{"pyth", "port", "pat"}}'.format(method))

    # ===================
    # Properties rankings
    # ===================

    @property
    def fisb(self):
        '''
        Returns FISB ranking.

        Returns
        -------
        ranking : pandas Series
        '''
        if not self._is_calced['FISB'] and not self._autocalc:
            print("Warning: FISB not calculated yet. \
                Use calc_ranking(method='fisb') to do so.")
        elif not self._is_calced['FISB'] and self._autocalc:
            print("Calculating FISB ranking now.")
            self.calc_ranking(method='fisb')
        return self._stats['FISB']

    @property
    def srs(self):
        '''
        Returns Simple Ranking System.

        Returns
        -------
        ranking : pandas DataFrame
            DataFrame with SRS, MoV and SoS.
        '''
        if not self._is_calced['SRS'] and not self._autocalc:
            print("Warning: SRS not calculated yet. \
                Use calc_ranking(method='srs') to do so.")
        elif not self._is_calced['SRS'] and self._autocalc:
            print("Calculating SRS now.")
            self.calc_ranking(method='srs')
        return self._stats[['SRS', 'MOV', 'SOS']]

    @property
    def ml(self):
        '''
        Returns Max-L ranking.

        Returns
        -------
        ranking : pandas Series
        '''
        if not self._is_calced['Max-L'] and not self._autocalc:
            print("Warning: Max-L not calculated yet. \
                Use calc_ranking(method='ml') to do so.")
        elif not self._is_calced['Max-L'] and self._autocalc:
            print("Calculating Max-L ranking now.")
            self.calc_ranking(method='ml')
        return self._stats['Max-L']

    # =======================
    # Properties Pythagoreans
    # =======================

    @property
    def pythagorean(self):
        if not self._is_calced['Pythagorean'] and not self._autocalc:
            print("Warning: Pythagorean not calculated yet. \
                Use calc_pythag('pyth') to do so.")
        elif not self._is_calced['Pythagorean'] and self._autocalc:
            print("Calculating Pythagorean now.")
            self.calc_pythag(method='pyth')
        return self._stats['Pythagorean']

    @property
    def pythagenport(self):
        if not self._is_calced['Pythagenport'] and not self._autocalc:
            print("Warning: Pythagenport not calculated yet. \
                Use calc_pythag('port') to do so.")
        elif not self._is_calced['Pythagenport'] and self._autocalc:
            print("Calculating Pythagenport now.")
            self.calc_pythag(method='port')
        return self._stats['Pythagenport']

    @property
    def pythagenpat(self):
        if not self._is_calced['Pythagenpat'] and not self._autocalc:
            print("Warning: Pythagenpat not calculated yet. \
                Use calc_pythag('pat') to do so.")
        elif not self._is_calced['Pythagenpat'] and self._autocalc:
            print("Calculating Pythagenpat now.")
            self.calc_pythag(method='pat')
        return self._stats['Pythagenpat']


if __name__ == '__main__':
    db_path = '/Users/andy/Documents/Football/NFL/nfl_games.db'
    games_query = 'select * from games where year=2012 and week<=17'
    games = fm_dl.from_sqlite(db_path, games_query)
    standings_query = 'select * from standings where year=2012 and week=17'
    standings = fm_dl.from_sqlite(db_path, standings_query)
    stats = Metrics(games, standings)
    stats.calc_ranking()
    print stats.fisb
