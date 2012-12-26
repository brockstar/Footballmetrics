from __future__ import division

import os
import multiprocessing as mp
import sqlite3

import numpy as np
import pandas as pd
# import some methods independently for faster decomposition
from numpy import shape, dot
from numpy.random import randint
from scipy.linalg import svd, diagsvd

import footballmetrics.dataloader as fm_dl


class FISB_Ranking(object):
    '''
    This class calculates a ranking similar to Sagarin's. It uses all
    games played in the season given by *year* and the given *week* 
    to determine a rating for every team and an additional home field advantage.
    There is also the possibility for a bootstrap of the results, so that
    the weight of potential outliers can be reduced.  
    '''
    def __init__(self, games_df):
        self._dh = fm_dl.DataHandler(games_df=games_df)
        self._teams = self._dh.get_teams()
        self._games = self._dh.get_games()

    def calculate_ranking(self, bootstrap_iterations=None, nprocs=2):
        '''
        Calculates the ranking based on the data loaded in ``load_data``.
        It uses a singular value decomposition (SVD) to decompose 
        the game matrix. It returns the ratings for each team and the 
        home field advantage.
        If *bootstrap_iterations* is set to an integer number, the game matrix will be 
        randomized as often as given in iteration. *nprocs* determines the number of 
        CPU cores used for computation.
        '''
        home_margins = self._dh.get_game_spreads()
        game_matrix = self._get_game_matrix()
        # _svd_filter is a simple function to invert the sigma vector of the decomposition.
        # It should be vectorized outside _decompose_matrix() for faster access.
        self._svd_filter = np.vectorize(lambda x: 0 if x < 1e-10 else 1 / x)
        if bootstrap_iterations is not None:
            try:
                random_results = self._bootstrap_games(game_matrix, home_margins, 
                        bootstrap_iterations, nprocs)
                x = np.mean(random_results, axis=0)
            except TypeError:
                raise TypeError('bootstrap_iterations and nprocs need to be integer numbers.')
        else:
            x = self._decompose_matrix(game_matrix, home_margins)
        ratings = pd.Series({team: rating for team, rating in zip(self._teams, x)})
        ratings = self._normalize(ratings)
        ratings = ratings.append(pd.Series({'Home field advantage': x[-1]}))
        return ratings           

    def _bootstrap_games(self, game_matrix, home_margins, iterations, nprocs=2):
        def worker(N, out_q):
            result = []
            for i in range(N):
                matrix, margins = self._randomize_matrix(game_matrix, home_margins)
                res = self._decompose_matrix(matrix, margins)
                result += [res]
            out_q.put(result)
        out_q = mp.Queue()
        N = int(np.ceil(iterations / nprocs))
        procs = []
        for i in range(nprocs):
            p = mp.Process(target=worker, args=(N, out_q, ))
            procs.append(p)
            p.start()
        results = []
        for i in range(nprocs):
            results += list(out_q.get())
        for p in procs:
            p.join()
        return results

    def _randomize_matrix(self, game_matrix, home_margins):
        rand_idx = randint(0, len(game_matrix), len(game_matrix))
        random_matrix = game_matrix[rand_idx]
        random_margins = home_margins[rand_idx]
        return random_matrix, random_margins
    
    def _get_game_matrix(self):
        # rows = games
        # columns = teams + home field advantage
        matrix = np.zeros((len(self._games), len(self._teams)+1))
        # To faster access index of every team create dict with indices for every team
        idx = {k: i for i, k in enumerate(self._teams)}
        get_idx = lambda team: idx[team]
        index_home = self._games['HomeTeam'].apply(get_idx)
        index_away = self._games['AwayTeam'].apply(get_idx)
        for i in range(len(self._games)):
            # game = home score - away score + home field advantage
            matrix[i, index_home[i]] = 1
            matrix[i, index_away[i]] = -1
            matrix[i, -1] = 1
        return matrix

    def _decompose_matrix(self, matrix, margins):
        # decompose game game_matrix using SVD
        U, s, Vh = svd(matrix)
        # extract singular values s and make diagonal game_matrix s_prime. 
        s = self._svd_filter(s)
        s_prime = diagsvd(s, shape(matrix)[1], shape(matrix)[0])
        # Ax = b --> x = A^(-1) * b = Vh_t * s_prime * U_t * b 
        # It looks a bit strange with np.dot but it's significantly faster than mat(Vh) * ...
        x = dot(dot(dot(Vh.T, s_prime), U.T), margins.T)
        return x

    def _normalize(self, ratings):
        ratings -= ratings.mean()
        return ratings


class ML_Ranking(object):
    def __init__(self, games_df, standings_df):
        '''
        This class produces Maximum-Likelihood rankings solely based on wins and losses.
        A dummy team is introduced, to assure finite ratings for unbeaten teams. It is easy to
        calculate a win probability with this model, since the probability for a victory of team A
        is: W(A) = R(A) / (R(A) + R(B)).
        The ratings will be calculated for all games played in season *year* up to week *week*.
        '''
        self._dh = fm_dl.DataHandler(games_df=games_df, standings_df=standings_df)
        self._teams = self._dh.get_teams()
        self._opponents = self._dh.get_opponents()

    def calculate_ranking(self, max_iter=100):
        '''
        Calculates the ranking. *max_iter* defines the maximal number of iterations before aborting.
        The other criterion for convergence is a sum-squared error of less than 1e-3.
        '''
        rating = {team: a for team, a in zip(self._teams, np.ones((len(self._teams))))}
        new_rating = rating.copy() 
        wins = self._dh.get_wins()
        dummy_rating = 1.0
        ssq = 1.0
        i = 0
        while ssq > 1e-3 and i < max_iter:
            for team in self._teams:
                denom = sum(1.0 / (rating[team] + rating[opp]) for opp in self._opponents[team])
                # dummy win and loss
                denom += 2.0 / (rating[team] + dummy_rating)
                new_rating[team] = (wins[team] + 1) / denom
            ssq = sum((rating[team] - new_rating[team]) ** 2 for team in rating)
            rating = new_rating.copy()
            i += 1
        if i == max_iter:
            print('Warning: Maximum number of iterations reached. Current sum squared error is {%3.3e}'.format(ssq))
        return pd.Series(rating)


class SRS(object):
    def __init__(self, games_df, standings_df):
        '''
        This class is capable of computing the Simple Rating System (SRS) for all teams
        in a given league. The SRS is simply the margin of victory (MoV) corrected by an value
        identified as strength of schedule (SOS). Hence, SRS = MoV + SOS.
        The ratings will be calculated for all games played in season *year* up to week *week*.
        '''
        self._dh = fm_dl.DataHandler(games_df=games_df, standings_df=standings_df)
        self._teams = self._dh.get_teams()
        self._opponents = self._dh.get_opponents()

    def calculate_ranking(self, method='normal', max_iter=100):
        '''
        This method calculates the rankings.
        The parameter *method* defines if the ordinary SRS or OSRS/DSRS is calculated.
        method = {'normal', 'offense', 'defense'}
        *max_iter* determines the maximal number of iterations before aborting. The other
        criterion of convergence is a sum-squared error of less than 1e-3.
        '''
        ssq = 1.
        n_games = dict(self._dh.get_number_of_games())
        if method == 'normal':
            mov = dict(self._dh.get_mov())
            srs = mov.copy()
        elif method == 'offense':
            # OSRS = Off_MoV + Def_SOS
            mov = dict(self._dh.get_scoring_over_avg(key='offense'))
            srs = dict(self._dh.get_scoring_over_avg(key='defense'))
        elif method == 'defense':
            # DSRS = Def_MoV + Off_SOS
            mov = dict(self._dh.get_scoring_over_avg(key='defense'))
            srs = dict(self._dh.get_scoring_over_avg(key='offense'))
        else:
            raise ValueError('Unknown method "{}".'.format(method))
        new_srs = {}
        i = 0
        calc_rating = lambda team: mov[team] + sum(srs[opp] for opp in self._opponents[team]) / n_games[team]
        while ssq > 1e-3 and i <= max_iter:
            new_srs = {team: calc_rating(team) for team in self._teams}
            ssq = sum((new_srs[team] - srs[team]) ** 2 for team in srs)
            srs = new_srs.copy()
            i += 1
        if i == max_iter:
            print('Warning: Maximum number of iterations reached. Current sum squared error is {%3.3e}'.format(ssq))
        sos = {team: srs[team] - mov[team] for team in srs}
        return srs, mov, sos
            
