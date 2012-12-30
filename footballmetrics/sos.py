from __future__ import division

import pandas as pd

import footballmetrics.dataloader as fm_dl


# TODO: Implement way to calculate SOS for upcoming games

class SOS(object):
    def __init__(self, schedule_df, standings_df):
        '''
        Implementation for different methods to calculate the strength of
        schedule (SOS).

        Parameters
        ----------
        schedule_df : pandas DataFrame
            Contains the games that go into calculation. Needed to determine
            opponents each team faced.
        standings_df : pandas DataFrame
            Contains standings for every team. Needed to determine number of
            games and wins for every team.

        Methods
        -------
        calculate

        Notes
        -----
        At the moment it's not possible to apply SOS to upcoming games.
        '''
        self._dh = fm_dl.DataHandler(games_df=schedule_df,
                                     standings_df=standings_df)
        self._teams = self._dh.get_teams()
        self._opponents = self._dh.get_opponents()

    def calculate(self, method='average', ratings=None):
        '''
        Calculates strength of schedule (SOS).

        Parameters
        ----------
        method : {'average', 'scaled', 'bcs'}
            Sets the method used for calculation. See Notes for details.
        ratings : dict, pandas Series
            Dict or Series containing ratings for each team. Only needed, if
            method is 'average' or 'scaled'.

        Returns
        -------
        sos : pandas Series
            Contains strength of schedule for each team.

        Notes
        -----
        Some remarks to the available methods for calculating SOS.

        'average'
            Uses ratings to determine SOS. Opponents cumulative ratings divided
            by number of games is value of SOS for a given team.
        'scaled'
            The same as 'average', but SOS is scaled as follows:
                scaled = (sos - r_min) / (r_max - r_min)
            Where r_max, r_min are maximal and minimal ratings found.
        'bcs'
            The formula from the Bowl Championship Series.
            It consists of the opponents win percentage (OP) and the opponent's
            opponents win percentage (OOP). It is calculated as follows:
                SOS = 2/3 * OP + 1/3 * OOP
        '''
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
        '''
        Private method.

        Calculates the SOS by adding opponents ratings and dividing it by
        number of games played.
        '''
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
        '''
        Private method.

        Similar to average method, but SOS is scaled based on minimal and
        maximal rating.
        '''
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
        '''
        Private method.

        Uses BCS formula to calculate BCS. Does not need ratings, but relies on
        opponents win percentage and opponent's opponent win percentage.
        '''
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
