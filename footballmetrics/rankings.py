from __future__ import division
import os
import random

import sqlite3
import numpy as np
import scipy.linalg
import scipy.optimize


class FISB_Ranking(object):
    '''
    This class calculates a ranking similar to Sagarin's. It uses all
    games played in the season given by *year* and the given *week* 
    to determine a rating for every team 
    and an additional home field advantage.
    There is also the possibility for a bootstrap of the results, so that
    the weight of potential outliers can be reduced.  
    '''
    def __init__(self, year, week, db_path, db_table='games'):
        self.year = year
        self.week = week
        self.__load_data(db_path, db_table)
                
    def __load_data(self, db_path, db_table):
        ''' Loads the data from a SQLite database at location *db_path*.'''
        if not os.path.isfile(db_path):
            print('Database file not found.')
        else:
            con = sqlite3.connect(db_path)
            with con:
                cur = con.cursor()
                if self.year is not None and self.week is not None:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                             from %s where Year=%d and Week<=%d''' % \
                             (db_table, self.year, self.week)
                elif self.year is not None and self.week is None:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                             from %s where Year=%d''' % (db_table, self.year)
                else:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                           from %s''' % (table)
                cur.execute(cmd)
                self.games = cur.fetchall()
            teams = []
            for game in self.games:
                if game[0] not in teams:
                    teams.append(str(game[0]))
                if game[1] not in teams:
                    teams.append(str(game[1]))
            self.teams = sorted(teams) 

    def calculate_ranking(self, bootstrapping=False, iterations=100):
        '''
        Calculates the ranking based on the data loaded in ``load_data``.
        It uses a singular value decomposition (SVD) to decompose 
        the game matrix. It returns the ratings for each team and the 
        home field advantage.
        If *bootstrapping* = True, the game matrix will be randomized as often
        as given in iteration.
        '''
        home_margins = self.__get_home_margins()
        game_matrix = self.__get_game_matrix()
        if bootstrapping and iterations > 0:
            random_x = []
            # randomly pick games and create new game matrix with these
            # randomized games
            for n in range(iterations):
                # list contains random indices of games to be chosen
                #random_list = []
                random_list = [random.randint(0, len(self.games)-1) 
                               for N in self.games]
                # generate a random game matrix and random home_margins
                # and solve the equation system for each iteration.
                random_game_matrix = np.zeros(game_matrix.shape)
                random_margins = np.zeros(home_margins.shape)
                for i in random_list:
                    random_game_matrix[i,:] = game_matrix[random_list[i], :]
                    random_margins[i] = home_margins[random_list[i]]
                random_x.append(self.__decompose_matrix(random_game_matrix,
                                                       random_margins))
            x = np.mean(random_x, axis=0)
        else:
            x = self.__decompose_matrix(game_matrix, home_margins)
        self.ratings = {}
        for i in range(len(self.teams)):
            self.ratings[self.teams[i]] = float(x[i])
        self.ratings = self.__normalize(self.ratings)
        self.ratings['Home field advantage'] = float(x[-1])
        return self.ratings           
    
    def __get_home_margins(self):
        home_margins = [float(x[-2]) - float(x[-1]) for x in self.games]
        return np.array(home_margins)

    def __get_game_matrix(self):
        # rows = games
        # columns = teams + home field advantage
        matrix = np.zeros((len(self.games), len(self.teams)+1))
        for i in range(matrix.shape[0]):
            index_home = self.teams.index(self.games[i][0])
            index_away = self.teams.index(self.games[i][1])
            # game = home score - away score + home field advantage
            matrix[i, index_home] = 1
            matrix[i, index_away] = -1
            matrix[i, -1] = 1
        return matrix
    
    def __decompose_matrix(self, matrix, margins, eps=1e-10):
        # decompose game game_matrix using SVD
        U, s, Vh = scipy.linalg.svd(matrix)
        # extract singular values s and make diagonal game_matrix s_prime. 
        # Set reciprocal of s to s_prime. Set s_prime to 0, if s < eps. 
        s_prime = scipy.linalg.diagsvd(s, matrix.shape[1], matrix.shape[0])
        for i in range(matrix.shape[1]-1):
            if s_prime[i,i] < eps:
                s_prime[i,i] = 0
            else:
                s_prime[i,i] = 1 / s_prime[i,i]
        # Ax = b --> x = A^(-1) * b = Vh_t * s_prime * U_t * b 
        x = np.mat(Vh).T * np.mat(s_prime) * np.mat(U).T * \
            np.mat(margins).T
        return x
    
    def __normalize(self, ratings):
        sum = 0.0
        for team in ratings.keys():
            sum += ratings[team]
        sum /= len(self.teams)
        for team in ratings.keys():
            ratings[team] -= sum
        return ratings


class ML_Ranking(object):
    def __init__(self, year, week, db_path, db_games_table='games', db_standings_table='standings'):
        self.year = year
        self.week = week
        self.db_path = db_path
        self.db_games_table = db_games_table
        self.db_standings_table = db_standings_table
        self.__load_data()

    def __load_data(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week<={}'.format(self.db_games_table, self.year, self.week))
        games = cur.fetchall()
        con.close()
        teams = []
        for game in games:
            if game[0] not in teams:
                teams.append(str(game[0]))
            if game[1] not in teams:
                teams.append(str(game[1]))
        self.teams = sorted(teams)
        self.team_games = {}
        for team in self.teams:
            self.team_games[team] = []
            for game in games:
                if str(game[0]) == team:
                    self.team_games[team] += [str(game[1])]
                elif str(game[1]) == team:
                    self.team_games[team] += [str(game[0])]

    def __get_wins(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select team, win from {} where year={} and week={}'.format(self.db_standings_table, self.year, self.week))
        team_wins = {}
        for row in cur.fetchall():
            team_wins[row[0]] = int(row[1])
        con.close()
        return team_wins

    def calculate_ranking(self):
        rating = dict(zip(self.teams, np.ones((len(self.teams)))))
        new_rating = {}
        wins = self.__get_wins()
        ssq = 1
        max_iter = 100
        i = 0
        dummy_rating = 1.0
        while ssq > 1e-3 and i < max_iter:
            for team in self.teams:
                denom = 0
                for opp in self.team_games[team]:
                    denom += 1.0 / (rating[team] + rating[opp])
                # dummy win and loss!!!
                denom += 2.0 / (rating[team] + dummy_rating)
                new_rating[team] = (wins[team] + 1) / denom
            ssq = 0.0
            for team in self.teams:
                ssq += (rating[team] - new_rating[team]) ** 2
                rating[team] = new_rating[team]
            i += 1
        return rating


class SRS(object):
    def __init__(self, year, week, db_path, db_games_table='games', db_standings_table='standings'):
        self.year = year
        self.week = week
        self.db_path = db_path
        self.db_games_table = db_games_table
        self.db_standings_table = db_standings_table
        self.__load_data()

    def __load_data(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week<={}'.format(self.db_games_table, self.year, self.week))
        games = cur.fetchall()
        con.close()
        teams = []
        for game in games:
            if game[0] not in teams:
                teams.append(str(game[0]))
            if game[1] not in teams:
                teams.append(str(game[1]))
        self.teams = sorted(teams)
        self.team_games = {}
        for team in self.teams:
            self.team_games[team] = []
            for game in games:
                if str(game[0]) == team:
                    self.team_games[team] += [str(game[1])]
                elif str(game[1]) == team:
                    self.team_games[team] += [str(game[0])]

    def __get_margin_of_victory(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select team, win, loss, tie, pointsfor, pointsagainst from {} where year={} and week={}'.format(self.db_standings_table, self.year, self.week))
        mov = {}
        n_games = {}
        for row in cur.fetchall():
            n_games[str(row[0])] = sum((int(row[1]), int(row[2]), int(row[3])))
            m = (int(row[4]) - int(row[5])) / n_games[str(row[0])]
            mov[str(row[0])] = m
        con.close()
        return mov, n_games

    def __get_offense_averages(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select team, win, loss, tie, pointsfor, pointsagainst from {} where year={} and week={}'.format(self.db_standings_table, self.year, self.week))
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

    def calculate_ranking(self, type='normal'):
        ssq = 1.
        max_iter = 100
        if type == 'normal':
            mov, n_games = self.__get_margin_of_victory()
            srs = mov.copy()
        elif type == 'offense':
            mov, def_mov, n_games = self.__get_offense_averages()
            srs = def_mov
        elif type == 'defense':
            off_mov, mov, n_games = self.__get_offense_averages()
            srs = off_mov
        new_srs = {}
        i = 0
        while ssq > 1e-3 and i <= max_iter:
            ssq = 0.0
            for team in self.teams:
                new_srs[team] = mov[team] + sum(srs[opp] for opp in self.team_games[team]) / n_games[team]
            for team in self.teams:
                ssq += (new_srs[team] - srs[team]) ** 2
                srs[team] = new_srs[team]
            i += 1
        if i == max_iter:
            print 'Warning: Maximum number of iterations reached. Current sum squared error is %3.3e' % ssq
        sos = {}
        for team in self.teams:
            sos[team] = srs[team] - mov[team]
        return srs, mov, sos
            

class CappedSRS(object):
    def __init__(self, year, week, db_path, db_games_table='games', db_standings_table='standings'):
        self.year = year
        self.week = week
        self.db_path = db_path
        self.db_games_table = db_games_table
        self.db_standings_table = db_standings_table
        self.__load_data()

    def __load_data(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week<={}'.format(self.db_games_table, self.year, self.week))
        games = cur.fetchall()
        con.close()
        teams = []
        for game in games:
            if game[0] not in teams:
                teams.append(str(game[0]))
            if game[1] not in teams:
                teams.append(str(game[1]))
        self.teams = sorted(teams)
        self.team_games = {}
        for team in self.teams:
            self.team_games[team] = []
            for game in games:
                if str(game[0]) == team:
                    self.team_games[team] += [str(game[1])]
                elif str(game[1]) == team:
                    self.team_games[team] += [str(game[0])]

    def __get_margin_of_victory(self, cap, weight):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select team, win, loss, tie, pointsfor, pointsagainst from {} where year={} and week={}'.format(self.db_standings_table, self.year, self.week))
        n_games = {}
        for row in cur.fetchall():
            n_games[str(row[0])] = sum((int(row[1]), int(row[2]), int(row[3])))
        if cap is not None:
            capped = lambda x: np.sign(x) * cap if abs(x) > cap else x
        else:
            capped = lambda x: x
        pts = {}
        cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore, Week from {} where year={} and week <= {}'.format('games', self.year, self.week))
        weighted = lambda x: weight ** (self.week - x)
        for row in cur.fetchall():
            pt_spread = weighted(int(row[4])) * (int(row[2]) - int(row[3]))
            if str(row[0]) in pts:
                pts[str(row[0])] += capped(pt_spread)
            else:
                pts[str(row[0])] = capped(pt_spread)
            if str(row[1]) in pts:
                pts[str(row[1])] += -1.0 * capped(pt_spread)
            else:
                pts[str(row[1])] = -1.0 * capped(pt_spread)
        mov = {}
        for team in pts.keys():
            mov[team] = pts[team] / n_games[team]
        con.close()
        return mov, n_games

    def __get_offense_averages(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select team, win, loss, tie, pointsfor, pointsagainst from {} where year={} and week={}'.format(self.db_standings_table, self.year, self.week))
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

    def calculate_ranking(self, type='normal', cap=None, weight=1.0):
        ssq = 1.
        max_iter = 100
        if type == 'normal':
            mov, n_games = self.__get_margin_of_victory(cap, weight)
            srs = mov.copy()
        elif type == 'offense':
            mov, def_mov, n_games = self.__get_offense_averages()
            srs = def_mov
        elif type == 'defense':
            off_mov, mov, n_games = self.__get_offense_averages()
            srs = off_mov
        new_srs = {}
        i = 0
        while ssq > 1e-3 and i <= max_iter:
            ssq = 0.0
            for team in self.teams:
                new_srs[team] = mov[team] + sum(srs[opp] for opp in self.team_games[team]) / n_games[team]
            for team in self.teams:
                ssq += (new_srs[team] - srs[team]) ** 2
                srs[team] = new_srs[team]
            i += 1
        if i == max_iter:
            print 'Warning: Maximum number of iterations reached. Current sum squared error is %3.3e' % ssq
        sos = {}
        for team in self.teams:
            sos[team] = srs[team] - mov[team]
        return srs, mov, sos

    def optimize_cap(self, x0=None):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week <= {}'.format('games', self.year, self.week))
        self.games = []
        scores = []
        for row in cur.fetchall():
            self.games.append([str(row[0]), str(row[1])])
            scores.append(int(row[2]) - int(row[3]))
        scores = np.array(scores)
        err = lambda x: ((scores - self.__helper_cap(x)) ** 2).sum()
        if x0 is None:
            x0 = [21, 3]
        err = lambda x: (self.__helper_cap(x) - scores)
        xopt = scipy.optimize.leastsq(err, x0)
        return xopt

    def optimize_weight(self, x0=None):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore from {} where year={} and week <= {}'.format('games', self.year, self.week))
        self.games = []
        scores = []
        for row in cur.fetchall():
            self.games.append([str(row[0]), str(row[1])])
            scores.append(int(row[2]) - int(row[3]))
        scores = np.array(scores)
        err = lambda x: ((scores - self.__helper_weight(x)) ** 2).sum()
        if x0 is None:
            x0 = [21, 3]
        err = lambda x: (self.__helper_weight(x) - scores)
        xopt = scipy.optimize.leastsq(err, x0)
        return xopt

    def __helper_cap(self, x):
        srs = self.calculate_ranking(cap=x[0])[0]
        srs_diff = []
        for game in self.games:
            srs_diff.append(srs[game[0]] - srs[game[1]] + x[1])
        return np.array(srs_diff)

    def __helper_weight(self, x):
        srs = self.calculate_ranking(weight=x[0])[0]
        srs_diff = []
        for game in self.games:
            srs_diff.append(srs[game[0]] - srs[game[1]] + x[1])
        return np.array(srs_diff)
                          
