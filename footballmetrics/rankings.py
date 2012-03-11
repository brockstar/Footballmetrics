from __future__ import division
import os
import random

import sqlite3
import numpy as np
import scipy.linalg


class FISB_Ratings:
    def __init__(self, year=2011, week=17):
        self.year = year
        self.week = week
                
    def loadData(self, db_path):
        if not os.path.isfile(db_path):
            raise IOError('Database file not found.')
        con = sqlite3.connect(db_path)
        with con:
            cur = con.cursor()
            cur.execute('select HomeTeam, AwayTeam, HomeScore, AwayScore from games where year=%d and week<=%d' % (self.year, self.week))
            self.games = cur.fetchall()
            cur.execute('select distinct HomeTeam, AwayTeam from games where year=%d and week=%d' % (self.year, self.week))
            res = cur.fetchall()
        teams = []
        for team in res:
            if team[0] not in teams:
                teams.append(str(team[0]).encode())
            if team[1] not in teams:
                teams.append(str(team[1]).encode())
        self.teams = sorted(teams)            
    
    def get_home_margins(self):
        home_margins = []
        for game in self.games:
            diff = float(game[-2]) - float(game[-1])
            home_margins.append(diff)
        return np.array(home_margins)
            
    def calc_sagarin(self):
        home_margins = self.get_home_margins()
        matrix = np.zeros( (len(self.games), len(self.teams)+1))
        for i in range(matrix.shape[0]):
            index_home = self.teams.index(self.games[i][0])
            index_away = self.teams.index(self.games[i][1])
            matrix[i, index_home] = 1
            matrix[i, index_away] = -1
            matrix[i, -1] = 1
        # decompose game matrix using SVD
        U, s, Vh = scipy.linalg.svd(matrix)
        M = matrix.shape[0]
        N = matrix.shape[1]
        # extract singular values s and make diagonal matrix s_prime. 
        # Set reciprocal of s to s_prime. Set s_prime to 0, if s < eps. 
        s_prime = scipy.linalg.diagsvd(s,N,M)
        eps = 1e-10
        for i in range(N-1):
            if s_prime[i,i] < eps:
                s_prime[i,i] = 0
            else:
                s_prime[i,i] = 1/s_prime[i,i]
        # Ax = b --> x = A^(-1) * b = Vh_t * s_prime * U_t * b 
        x = np.mat(Vh).T * np.mat(s_prime) * np.mat(U).T * np.mat(home_margins).T
        self.ratings = {}
        for i in range(len(self.teams)):
            self.ratings[self.teams[i]] = float(x[i])
        self.sagarin_correction()
        self.ratings['Home field advantage'] = float(x[-1])
        return self.ratings
    
    def sagarin_correction(self):
        sum = 0.0
        for i in self.teams:
            sum += self.ratings[i]

        sum /= len(self.teams)
        for i in self.teams:
            self.ratings[i] -= sum
            
    
class oldSagarin:
    def __init__(self):
        self.teams = {}
        self.rating = {}
        self.home_advantage = 0.
        self.home_team = []
        self.away_team = []
        self.home_score = []
        self.away_score = []
              
                
    def loadData(self, a):
        temp_team = []
        
        for i in np.arange(np.shape(a)[0]):
            if str(a[i][0]) not in temp_team:
                temp_team.append(str(a[i][0]))
            if str(a[i][2]) not in temp_team:
                temp_team.append(str(a[i][2]))
        
        temp_team.sort()
        for i in np.arange(0, len(temp_team)):
            self.teams[temp_team[i]] = i

        for i in np.arange(0, np.shape(a)[0]):
            self.home_team.append(self.teams[a[i][0]])
            self.away_team.append(self.teams[a[i][2]])
            self.home_score.append(np.double(a[i][1]))
            self.away_score.append(np.double(a[i][3]))

            
    def calc_sagarin(self):
        home_margins = []
        for i in np.arange(0, len(self.home_team)):
            hm = int(self.home_score[i]) - int(self.away_score[i])
            home_margins.append(hm)
        home_margins = np.array(home_margins)
        
        matrix = np.zeros( (len(self.home_team), len(self.teams)+1))
        for i in np.arange(0, len(self.home_team)):
            index_home = self.home_team[i]
            index_away = self.away_team[i]
            matrix[i, index_home] = 1
            matrix[i, index_away] = -1
            matrix[i, -1] = 1
            
        U, s, Vh = scipy.linalg.svd(matrix)
        
        M = np.shape(matrix)[0]
        N = np.shape(matrix)[1]
        s_prime = scipy.linalg.diagsvd(s,N,M)

        eps = 1e-10
        for i in range(N-1):
            if s_prime[i,i] < eps:
                s_prime[i,i] = 0
            else:
                s_prime[i,i] = 1/s_prime[i,i]

        x = np.mat(Vh).T * np.mat(s_prime) * np.mat(U).T * np.mat(home_margins).T

        self.rankings = np.zeros((33))
        for i in range(len(x)):
            self.rankings[i] = x[i]
        
        for i in self.teams:
            self.rating[i] = x[self.teams[i]]
        self.home_advantage = x[len(self.teams)]
        
        self.sagarin_correction()
            
    
    def bootstrap_calc_sagarin(self, max_iter):
        home_margins = []
        for i in np.arange(0, len(self.home_team)):
            hm = int(self.home_score[i]) - int(self.away_score[i])
            home_margins.append(hm)
        home_margins = np.array(home_margins)
        
        matrix = np.zeros( (len(self.home_team), len(self.teams)+1))
        for i in np.arange(0, len(self.home_team)):
            index_home = self.home_team[i]
            index_away = self.away_team[i]
            matrix[i, index_home] = 1
            matrix[i, index_away] = -1
            matrix[i, -1] = 1

        rankings = np.zeros((33,max_iter))
        for i in np.arange(0, max_iter):
            rnd = np.empty((len(self.home_team),))
            for j in np.arange (0,len(rnd)):
                rnd[j] = random.randint(0, len(rnd)-1)
        
            matrix_var = np.zeros(np.shape(matrix))
            margins_var = np.zeros(np.shape(home_margins))
            for j in np.arange(0, len(rnd)):
                matrix_var[j,:] = matrix[rnd[j],:]
                margins_var[j] = home_margins[rnd[j]]
        
            U, s, Vh = scipy.linalg.svd(matrix_var)
        
            M = np.shape(matrix_var)[0]
            N = np.shape(matrix_var)[1]
            s_prime = scipy.linalg.diagsvd(s,N,M)

            eps = 1e-10
            for j in range(N-1):
                if s_prime[j,j] < eps:
                    s_prime[j,j] = 0
                else:
                    s_prime[j,j] = 1/s_prime[j,j]

            x = np.mat(Vh).T * np.mat(s_prime) * np.mat(U).T * np.mat(margins_var).T
        
            for j in np.arange(0,len(x)):
                rankings[j,i] = x[j]

        self.rankings = rankings
        ranking_mean = np.zeros((33))
        for i in np.arange(0,len(ranking_mean)):
            ranking_mean[i] = np.mean(rankings[i][:])
            
        for i in self.teams:
            self.rating[i] = ranking_mean[self.teams[i]]
        self.home_advantage = x[len(self.teams)]
   
        self.sagarin_correction()
    
            
    def sagarin_correction(self):
        sum = 0.0
        for i in self.teams:
            sum += self.rating[i]

        sum /= len(self.teams)
        for i in self.teams:
            self.rating[i] -= sum
            
if __name__ == '__main__':
    db = '/Users/andy/Documents/python/Footballmetrics/nfl_games.db'
    sag = FISB_Ratings(year=2011, week=17)
    sag.loadData(db)
    res = sag.calc_sagarin()
    for key in sorted(res.keys()):
        if key != 'Home field advantage':
            print '%s\t%3.2f' % (key, res[key])
    print '\n%s\t%3.2f' % ('Home field advantage', res['Home field advantage'])