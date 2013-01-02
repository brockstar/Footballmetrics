from __future__ import division

import multiprocessing as mp

import numpy as np
import pandas as pd
# import some methods independently for faster decomposition
from numpy import shape, dot
from numpy.random import randint
from scipy.linalg import svd, diagsvd

import footballmetrics.dataloader as fm_dl


# TODO: Add methods to calculate win probability directly


class FISB_Ranking(object):
    def __init__(self, games_df):
        '''
        Implementation of Sagarin's rankings. It uses the point spread
        in every single game played and calculates a ranking for every team
        and a global homefield advantage.

        Parameters
        ----------
        games_df : pandas DataFrame, footballmetrics.DataLoader
                DataFrame containing all games that shall be included
                in computation. Needs to have following columns:
                    [HomeTeam, AwayTeam, HomeScore, AwayScore].

        See also
        --------
        ML_Ranking, SRS
        '''
        self._initialize(games_df)

    def _initialize(self, games_df):
        self._dh = fm_dl.DataHandler(games_df=games_df)
        self._teams = self._dh.get_teams()
        self._games = self._dh.get_games()

    def set_games_df(self, games_df):
        '''
        Sets the games_df without reinitializing the object.

        Parameters
        ----------
        games_df : pandas DataFrame, footballmetrics.DataLoader
                DataFrame containing all games that shall be included
                in computation. Needs to have following columns:
                    [HomeTeam, AwayTeam, HomeScore, AwayScore].
        '''
        self._initialize(games_df)

    def calculate_ranking(self, bootstrap_iterations=None, nprocs=2):
        '''
        Calculates the rankings.

        Parameters
        ----------
        bootstrap_iterations : None, int
            If set to an integer value x, the game matrix will be randomized
            x-times and be solved independently. The rankings are returned as
            the means from the bootstrapping.
            If set to None only the input game matrix will be solved.
        nprocs : int
            Number of cores used for calculating the ranking.
            Only applied when bootstrapping is used.

        Returns
        -------
        ratings : pandas Series
            This pandas Series contains the ratings with the team names
            as index.
        '''
        home_margins = self._dh.get_game_spreads()
        game_matrix = self._get_game_matrix()
        # _svd_filter is a simple function to invert the sigma vector
        # of the decomposition.
        # It should be vectorized outside _decompose_matrix() for faster access.
        self._svd_filter = np.vectorize(lambda x: 0 if x < 1e-10 else 1 / x)
        if bootstrap_iterations is not None:
            try:
                random_results = self._bootstrap_games(game_matrix,
                                                       home_margins,
                                                       bootstrap_iterations,
                                                       nprocs)
                x = np.mean(random_results, axis=0)
            except TypeError:
                raise TypeError('bootstrap_iterations and nprocs need to be \
                    integer numbers.')
        else:
            x = self._decompose_matrix(game_matrix, home_margins)
        ratings = {team: rating for team, rating in zip(self._teams, x)}
        ratings = pd.Series(ratings)
        ratings = self._normalize(ratings)
        ratings = ratings.append(pd.Series({'Home field advantage': x[-1]}))
        return ratings

    def _bootstrap_games(self, game_matrix, home_margins, iterations, nprocs=2):
        '''
        Private method.

        Handles the multiprocessing of bootstrapping.

        Parameters
        ----------
        game_matrix : np.ndarray
            Two-dimensional array containing games.
        home_margins : np.ndarray, pandas Series
            One-dimensional array (or Series) containing point spread of every
            game.
        iterations : int
            Number of bootstrap iterations to be performed.
        nprocs : int
            Number of cores used for calculation.

        Returns
        -------
        result : list
            List with (# of iterations) elements. Each element is result of a
            single decomposition.
        '''
        def worker(N, out_q):
            result = []
            for i in range(N):
                matrix, margins = self._randomize_matrix(game_matrix,
                                                         home_margins)
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
        '''
        Randomizes/Resamples game matrix.

        Parameters
        ----------
        game_matrix : np.ndarray
            Two-dimensional array containing games.
        home_margins : np.ndarray, pandas Series
            One-dimensional array (or Series) containing point spread of every
            game.

        Returns
        -------
        random_matrix : np.ndarray
            Two-dimensional array with resampled game matrix
        random_margins : np.ndarray, pandas Series
            One-dimensional array (or Series) with resampled home margins.
        '''
        rand_idx = randint(0, len(game_matrix), len(game_matrix))
        random_matrix = game_matrix[rand_idx]
        random_margins = home_margins[rand_idx]
        return random_matrix, random_margins

    def _get_game_matrix(self):
        '''
        Returns game matrix.

        Parameters
        ----------
        None

        Returns
        -------
        matrix : np.ndarray
            Two-dimensional array with matrix representation of games found in
            data.
        '''
        # rows = games
        # columns = teams + home field advantage
        matrix = np.zeros((len(self._games), len(self._teams) + 1))
        # To faster access index of every team create dict
        # with indices for every team.
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
        '''
        Decomposes game matrix.

        Parameters
        ----------
        matrix : np.ndarray
            Game matrix (2-dim).
        margins : np.ndarray, pandas Series
            Point spreads for every game (1-dim).

        Returns
        -------
        x : np.ndarray
            One-dimensional array containing rating for every team.
        '''
        # Decompose game game_matrix using SVD
        U, s, Vh = svd(matrix)
        # Extract singular values s and make diagonal game_matrix s_prime.
        s = self._svd_filter(s)
        s_prime = diagsvd(s, shape(matrix)[1], shape(matrix)[0])
        # Ax = b --> x = A^(-1) * b = Vh_t * s_prime * U_t * b
        # It looks a bit strange with np.dot, but it's significantly
        # faster than mat(Vh) * ...
        x = dot(dot(dot(Vh.T, s_prime), U.T), margins.T)
        return x

    def _normalize(self, ratings):
        '''
        Normalizes ratings, so that mean is zero.

        Parameters
        ----------
        ratings : np.ndarray, pandas Series
            Ratings for every team (without home field advantage).

        Returns
        -------
        norm_rating : np.ndarray, pandas Series
            Normalized ratings.
        '''
        norm_ratings = ratings - ratings.mean()
        return norm_ratings


class ML_Ranking(object):
    def __init__(self, games_df, standings_df):
        '''
        Implementation of a maximum-likelihood ranking system
        solely based on wins and losses.
        A dummy team is introduced, to assure finite ratings for unbeaten teams.
        It is easy to calculate a win probability with this model.
        The probability for a victory of team A is:
            W(A) = R(A) / (R(A) + R(B)).

        Parameters
        ----------
        games_df : pandas DataFrame, footballmetrics.DataLoader
            DataFrame or DataLoader object containing all games that shall
            be included in computation. Needs to have following columns:
            [HomeTeam, AwayTeam].
        standings_df : pandas DataFrame, footballmetrics.DataLoader
            DataFrame or DataLoader object containing the standings for all
            teams. Following columns need to be in it:
            [Win, Loss, Tie]

        See also
        --------
        FISB_Ranking, SRS
        '''
        self._dh = fm_dl.DataHandler(games_df=games_df,
                                     standings_df=standings_df)
        self._teams = self._dh.get_teams()
        self._opponents = self._dh.get_opponents()

    def calculate_ranking(self, max_iter=100):
        '''
        Calculates the ranking.

        Parameters
        ----------
        max_iter : int
            Maximum number of iterations.

        Returns
        -------
        ratings : pandas Series
            This Series contains the ratings with the team names as index.

        Notes
        -----
        Besides the maximum number of iterations there is the sum squared error
        as additional convergence criterion.
        If SSE < 1e-3 the iteration will terminate, too.
        '''
        rating = {team: a for team, a in zip(self._teams,
            np.ones((len(self._teams))))}
        new_rating = rating.copy()
        wins = self._dh.get_wins()
        dummy_rating = 1.0
        ssq = 1.0
        i = 0
        while ssq > 1e-3 and i < max_iter:
            for team in self._teams:
                denom = sum(1.0 / (rating[team] + rating[opp]) for opp
                    in self._opponents[team])
                # dummy win and loss
                denom += 2.0 / (rating[team] + dummy_rating)
                new_rating[team] = (wins[team] + 1) / denom
            ssq = sum((rating[team] - new_rating[team]) ** 2 for team in rating)
            rating = new_rating.copy()
            i += 1
        if i == max_iter:
            print('Warning: Maximum number of iterations reached. \
                Current sum squared error is {%3.3e}'.format(ssq))
        return pd.Series(rating)


class SRS(object):
    def __init__(self, games_df, standings_df):
        '''
        Implementation of the Simple Ranking System (SRS).
        It is based on the margins of victory (MoV) for every team.
        The rating can be interpreted as follows:
        SRS = MoV + SOS
        Here, SOS is the strength of schedule.

        Parameters
        ----------
        games_df : pandas DataFrame, footballmetrics.DataLoader
            DataFrame or DataLoader object containing all games that shall
            be included in computation. Needs to have following columns:
            [HomeTeam, AwayTeam].
        standings_df : pandas DataFrame, footballmetrics.DataLoader
            DataFrame or DataLoader object containing the standings for all
            teams. Following columns need to be in it:
            [Win, Loss, Tie]

        See also
        --------
        FISB_Ranking, ML_Ranking
        '''
        self._dh = fm_dl.DataHandler(games_df=games_df,
                                     standings_df=standings_df)
        self._teams = self._dh.get_teams()
        self._opponents = self._dh.get_opponents()

    def calculate_ranking(self, method='normal', max_iter=100):
        '''
        Calculates the rankings.

        Parameters
        ----------
        method : {'normal', 'offense', 'defense'}
            Switches between normal SRS, offense SRS (OSRS) and
            defense SRS (DSRS).
        max_iter: int
            Maximum number of iterations.

        Returns
        -------
        srs : dict
            Contains the ratings for each team.
        mov : dict
            Contains the margin of victory (MoV) for each team.
        sos : dict
            Contains the strength of schedule (SOS) for each team.

        Notes
        -----
        Besides the maximum number of iterations there is the sum squared error
        as additional convergence criterion.
        If SSE < 1e-3 the iteration will terminate, too.
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
        calc_rating = lambda team: mov[team] + sum(srs[opp] for opp in
            self._opponents[team]) / n_games[team]
        while ssq > 1e-3 and i <= max_iter:
            new_srs = {team: calc_rating(team) for team in self._teams}
            ssq = sum((new_srs[team] - srs[team]) ** 2 for team in srs)
            srs = new_srs.copy()
            i += 1
        if i == max_iter:
            print('Warning: Maximum number of iterations reached. \
                Current sum squared error is {%3.3e}'.format(ssq))
        sos = {team: srs[team] - mov[team] for team in srs}
        return srs, mov, sos
