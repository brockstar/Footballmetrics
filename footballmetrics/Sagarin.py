from __future__ import division

import numpy as np
from scipy.linalg import svd, diagsvd
import random


class Sagarin:
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
            
        U, s, Vh = svd(matrix)
        
        M = np.shape(matrix)[0]
        N = np.shape(matrix)[1]
        s_prime = diagsvd(s,N,M)

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
        
            U, s, Vh = svd(matrix_var)
        
            M = np.shape(matrix_var)[0]
            N = np.shape(matrix_var)[1]
            s_prime = diagsvd(s,N,M)

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