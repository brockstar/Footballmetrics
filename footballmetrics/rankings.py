from __future__ import division

import os
import multiprocessing as mp
import sqlite3

import numpy as np
# import some methods independently for faster decomposition
from numpy import shape, dot
from numpy.random import randint
from scipy.linalg import svd, diagsvd


class FISB_Ranking(object):
    '''
    This class calculates a ranking similar to Sagarin's. It uses all
    games played in the season given by *year* and the given *week* 
    to determine a rating for every team and an additional home field advantage.
    There is also the possibility for a bootstrap of the results, so that
    the weight of potential outliers can be reduced.  
    '''
    __slots__ = ['_year', '_week', '_games', '_teams', '_svd_filter']
    def __init__(self, year, week, db_path, db_table='games'):
        self._year = year
        self._week = week
        self._load_data(db_path, db_table)
                
    def _load_data(self, db_path, db_table):
        ''' Loads the data from a SQLite database at location *db_path*.'''
        if os.path.isfile(db_path):
            con = sqlite3.connect(db_path)
            with con:
                cur = con.cursor()
                if self._year is not None and self._week is not None:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                             from %s where Year=%d and Week<=%d''' % \
                             (db_table, self._year, self._week)
                elif self._year is not None and self._week is None:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                             from %s where Year=%d''' % (db_table, self._year)
                else:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                           from %s''' % (db_table)
                cur.execute(cmd)
                self._games = cur.fetchall()
            teams = []
            for game in self._games:
                if game[0] not in teams:
                    teams.append(str(game[0]))
                if game[1] not in teams:
                    teams.append(str(game[1]))
            self._teams = sorted(teams)
        else:
            raise IOError('Database not found.')

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
        home_margins = self._get_home_margins()
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
        ratings = {team: rating for team, rating in zip(self._teams, x)}
        ratings = self._normalize(ratings)
        ratings['Home field advantage'] = x[-1]
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
    
    def _get_home_margins(self):
        home_margins = np.array([float(x[-2]) - float(x[-1]) for x in self._games])
        return home_margins

    def _get_game_matrix(self):
        # rows = games
        # columns = teams + home field advantage
        matrix = np.zeros((len(self._games), len(self._teams)+1))
        # To faster access index of every team create dict with indices for every team
        idx = {k: i for i, k in enumerate(self._teams)}
        for i in xrange(matrix.shape[0]):
            index_home = idx[self._games[i][0]]
            index_away = idx[self._games[i][1]]
            # game = home score - away score + home field advantage
            matrix[i, index_home] = 1
            matrix[i, index_away] = -1
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
        rating_sum = np.sum(list(ratings.values())) / len(self._teams) 
        ratings = {k: v - rating_sum for k, v in ratings.items()}
        return ratings


class ML_Ranking(object):
    def __init__(self, year, week, db_path, db_games_table='games', db_standings_table='standings'):
        '''
        This class produces Maximum-Likelihood rankings solely based on wins and losses.
        A dummy team is introduced, to assure finite ratings for unbeaten teams. It is easy to
        calculate a win probability with this model, since the probability for a victory of team A
        is: W(A) = R(A) / (R(A) + R(B)).
        The ratings will be calculated for all games played in season *year* up to week *week*.
        '''
        self._year = year
        self._week = week
        self._db_path = db_path
        self._db_games_table = db_games_table
        self._db_standings_table = db_standings_table
        self._load_data()

    def _load_data(self):
        con = sqlite3.connect(self._db_path)
        cur = con.cursor()
        if self._year is None:
            cmd = 'select HomeTeam, AwayTeam, HomeScore, AwayScore from {}'.format(self._db_games_table)
        else: 
            cmd = 'select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week<={}'.format(self._db_games_table, self._year, self._week)
        cur.execute(cmd)
        games = cur.fetchall()
        con.close()
        teams = []
        for game in games:
            if game[0] not in teams:
                teams.append(str(game[0]))
            if game[1] not in teams:
                teams.append(str(game[1]))
        self._teams = sorted(teams)
        self._team_games = {}
        for team in self._teams:
            self._team_games[team] = []
            for game in games:
                if str(game[0]) == team:
                    self._team_games[team] += [str(game[1])]
                elif str(game[1]) == team:
                    self._team_games[team] += [str(game[0])]

    def _get_wins(self):
        con = sqlite3.connect(self._db_path)
        with con:
            cur = con.cursor()
            if self._year is None:
                cmd = 'select team, win from {}'.format(self._db_standings_table)
            else:
                cmd = 'select team, win from {} where year={} and week={}'.format(self._db_standings_table, self._year, self._week)
            team_wins = {row[0]: int(row[1]) for row in cur.execute(cmd)}
        return team_wins

    def calculate_ranking(self, max_iter=100):
        '''
        Calculates the ranking. *max_iter* defines the maximal number of iterations before aborting.
        The other criterion for convergence is a sum-squared error of less than 1e-3.
        '''
        rating = {team: a for team, a in zip(self._teams, np.ones((len(self._teams))))}
        new_rating = rating.copy() 
        wins = self._get_wins()
        dummy_rating = 1.0
        ssq = 1.0
        i = 0
        team_games = self._team_games
        while ssq > 1e-3 and i < max_iter:
            for team in self._teams:
                denom = sum(1.0 / (rating[team] + rating[opp]) for opp in team_games[team])
                # dummy win and loss
                denom += 2.0 / (rating[team] + dummy_rating)
                new_rating[team] = (wins[team] + 1) / denom
            ssq = sum((rating[team] - new_rating[team]) ** 2 for team in rating)
            rating = new_rating.copy() 
            i += 1
        if i == max_iter:
            print('Warning: Maximum number of iterations reached. Current sum squared error is {%3.3e}'.format(ssq))
        return rating


class SRS(object):
    def __init__(self, year, week, db_path, db_games_table='games', db_standings_table='standings'):
        '''
        This class is capable of computing the Simple Rating System (SRS) for all teams
        in a given league. The SRS is simply the margin of victory (MoV) corrected by an value
        identified as strength of schedule (SOS). Hence, SRS = MoV + SOS.
        The ratings will be calculated for all games played in season *year* up to week *week*.
        '''
        self._year = year
        self._week = week
        self.db_path = db_path
        self.db_games_table = db_games_table
        self.db_standings_table = db_standings_table
        self._load_data()

    def _load_data(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        if self._year is None:
            cmd = 'select HomeTeam, AwayTeam, HomeScore, AwayScore from {}'.format(self.db_games_table)
        else:
            cmd = 'select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week<={}'.format(self.db_games_table, self._year, self._week)
        cur.execute(cmd)
        games = cur.fetchall()
        con.close()
        teams = []
        for game in games:
            if game[0] not in teams:
                teams.append(str(game[0]))
            if game[1] not in teams:
                teams.append(str(game[1]))
        self._teams = sorted(teams)
        self.team_games = {}
        for team in self._teams:
            self.team_games[team] = []
            for game in games:
                if str(game[0]) == team:
                    self.team_games[team] += [str(game[1])]
                elif str(game[1]) == team:
                    self.team_games[team] += [str(game[0])]

    def _get_margin_of_victory(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        if self._year is None:
            cmd = 'select team, win, loss, tie, pointsfor, pointsagainst from {}'.format(self.db_standings_table)
        else:
            cmd = 'select team, win, loss, tie, pointsfor, pointsagainst from {} where year={} and week={}'.format(self.db_standings_table, self._year, self._week)
        cur.execute(cmd)
        mov = {}
        n_games = {}
        for row in cur.fetchall():
            n_games[str(row[0])] = sum((int(row[1]), int(row[2]), int(row[3])))
            m = (int(row[4]) - int(row[5])) / n_games[str(row[0])]
            mov[str(row[0])] = m
        con.close()
        return mov, n_games

    def _get_offense_averages(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        if self._year is None:
            cmd = 'select team, win, loss, tie, pointsfor, pointsagainst from {}'.format(self.db_standings_table)
        else:
            cmd = 'select team, win, loss, tie, pointsfor, pointsagainst from {} where year={} and week={}'.format(self.db_standings_table, self._year, self._week)
        cur.execute(cmd)
        points_for = {}
        points_against = {}
        n_games = {}
        for row in cur.fetchall():
            n_games[str(row[0])] = sum((int(row[1]), int(row[2]), int(row[3])))
            pf = int(row[4]) / n_games[str(row[0])]
            points_for[str(row[0])] = pf
            pa = int(row[5]) / n_games[str(row[0])]
            points_against[str(row[0])] = pa
        pf_avg = np.mean(points_for.values())
        pa_avg = np.mean(points_against.values())
        for team in points_for.keys():
            points_for[team] -= pf_avg
            points_against[team] -= pa_avg
        con.close()
        return points_for, points_against, n_games

    def calculate_ranking(self, method='normal', max_iter=100):
        '''
        This method calculates the rankings.
        The parameter *method* defines if the ordinary SRS or OSRS/DSRS is calculated.
        method = {'normal', 'offense', 'defense'}
        *max_iter* determines the maximal number of iterations before aborting. The other
        criterion of convergence is a sum-squared error of less than 1e-3.
        '''
        ssq = 1.
        if method == 'normal':
            mov, n_games = self._get_margin_of_victory()
            srs = mov.copy()
        elif method == 'offense':
            mov, def_mov, n_games = self._get_offense_averages()
            srs = def_mov
        elif method == 'defense':
            off_mov, mov, n_games = self._get_offense_averages()
            srs = off_mov
        else:
            raise ValueError('Unknown method "{}".'.format(method))
        new_srs = {}
        i = 0
        calc_rating = lambda team: mov[team] + sum(srs[opp] for opp in self.team_games[team]) / n_games[team]
        while ssq > 1e-3 and i <= max_iter:
            new_srs = {team: calc_rating(team) for team in self._teams}
            ssq = sum((new_srs[team] - srs[team]) ** 2 for team in srs)
            srs = new_srs.copy()
            i += 1
        if i == max_iter:
            print('Warning: Maximum number of iterations reached. Current sum squared error is {%3.3e}'.format(ssq))
        sos = {team: srs[team] - mov[team] for team in srs}
        return srs, mov, sos
            
