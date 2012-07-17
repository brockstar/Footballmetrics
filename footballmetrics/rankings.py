from __future__ import division
import os
import random

import sqlite3
import numpy as np
import scipy.linalg


class FISB_Ranking:
    '''
    This class calculates a ranking similar to Sagarin's. It uses all
    games played in the season given by *year* and the given *week* 
    to determine a rating for every team 
    and an additional home field advantage.
    There is also the possibility for a bootstrap of the results, so that
    the weight of potential outliers can be reduced.  
    '''
    def __init__(self, year=None, week=None):
        self.year = year
        self.week = week
                
    def load_data(self, db_path, table='games'):
        ''' Loads the data from a SQLite database at location *db_path*.'''
        if not os.path.isfile(db_path):
            print 'Database file not found.'
        else:
            con = sqlite3.connect(db_path)
            with con:
                cur = con.cursor()
                if self.year is not None and self.week is not None:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                             from %s where Year=%d and Week<=%d''' % \
                             (table, self.year, self.week)
                elif self.year is not None and self.week is None:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                             from %s where Year=%d''' % (table, self.year)
                else:
                    cmd = '''select HomeTeam, AwayTeam, HomeScore, AwayScore
                           from %s''' % (table)
                cur.execute(cmd)
                self.games = cur.fetchall()
            teams = []
            for game in self.games:
                if game[0] not in teams:
                    teams.append(str(game[0]).encode())
                if game[1] not in teams:
                    teams.append(str(game[1]).encode())
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
            for n in xrange(iterations):
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
        for i in xrange(len(self.teams)):
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
        for i in xrange(matrix.shape[0]):
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
        for i in xrange(matrix.shape[1]-1):
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
        for team in ratings.iterkeys():
            sum += ratings[team]
        sum /= len(self.teams)
        for team in ratings.iterkeys():
            ratings[team] -= sum
        return ratings
