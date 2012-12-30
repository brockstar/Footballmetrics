from __future__ import division

import pandas as pd

import footballmetrics.dataloader as fm_dl


class SOS(object):
    def __init__(self, schedule_df, standings_df):
        self._dh = fm_dl.DataHandler(games_df=schedule_df,
                                     standings_df=standings_df)
        self._teams = self._dh.get_teams()
        self._opponents = self._dh.get_opponents()

    def calculate(self, method='average', ratings=None):
        if method == 'average':
            if ratings is not None:
                return self._calc_avg(ratings)
            else:
                raise ValueError('average method requires ratings.')
        elif method == 'scaled':
            if ratings is not None:
                return self._calc_scaled_avg(ratings)
            else:
                raise ValueError('average method requires ratings.')
        elif method == 'bcs':
            return self._calc_bcs()
        else:
            raise ValueError("method must be in {'average', 'scaled', 'bcs'}")

    def _calc_avg(self, ratings):
        if not type(ratings) in [dict, pd.core.series.Series]:
            raise ValueError('ratings must be dict or pandas Series.')
        sos = {}
        for team in self._teams:
            opp_ratings = sum(ratings[opp] for opp in self._opponents[team])
            avg_rating = opp_ratings / len(self._opponents[team])
            sos[team] = avg_rating
        sos = pd.Series(sos)
        return sos

    def _calc_scaled_avg(self,ratings):
        sos = self._calc_avg(ratings)
        if type(ratings) == pd.core.series.Series:
            r_min = ratings.min()
            r_max = ratings.max()
        else:
            r_min = min(ratings.values())
            r_max = max(ratings.values())
        scaling = lambda x: (x - r_min) / (r_max - r_min)
        scaled_sos = sos.apply(scaling)
        return scaled_sos

    def _calc_bcs(self):
        wins = self._dh.get_wins()
        ngames = self._dh.get_number_of_games()
        sos = {}
        for team in self._teams:
            opp_wins =  sum(wins[self._opponents[team]])
            opp_ngames = sum(ngames[self._opponents[team]])
            opp_wlp = opp_wins / opp_ngames
            opp_opp_wins = sum(sum(wins[self._opponents[opp]]) for opp in
                    self._opponents[team])
            opp_opp_ngames = sum(sum(ngames[self._opponents[opp]]) for opp in
                    self._opponents[team])
            opp_opp_wlp = opp_opp_wins / opp_opp_ngames
            sos[team] = 2/3 * opp_wlp + 1/3 * opp_opp_wlp
        sos = pd.Series(sos)
        return sos
