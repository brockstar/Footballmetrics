from __future__ import division

import numpy as np
from scipy.linalg import svd, diagsvd
from scipy.optimize import brent, bracket, fmin
import random
from IPython import embed
    
# ranking systems
# ===============


# Sagarin rankings
# ----------------
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


# Pythagorean expectation in football 
# -----------------------------------
class PythagoreanExpectation:
    def __init__(self):
        self.teams = []
        self.points_allowed = []
        self.points_for = []
        self.win_loss_per = []
        self.power = 0.
        self.prediction = []
        
    
    def loadData(self, d):
        self.teams = d['teams']
        self.points_allowed = np.double(d['points_allowed'])
        self.points_for = np.double(d['points_for'])
        self.win_loss_per = np.double(d['wlp'])

    
    def helper(self, x):
        ssq = 0.
        f = lambda x_,pf_,pa_: pf_**x_ / (pf_**x_ + pa_**x_)
        for i in np.arange(0, len(self.teams)):
            calc = f(x, self.points_for[i], self.points_allowed[i])
            ssq += (self.win_loss_per[i] - calc)**2
        
        return ssq
        
        
    def calc_pyth(self):
        xa, xb, xc, fa, fb, fc, calls = bracket(self.helper)
        self.power = brent(self.helper, brack=(xa,xb,xc))
        f = lambda x,pf,pa: pf**x / (pf**x + pa**x)
        for i in np.arange(0, len(self.teams)):
            self.prediction.append(f(self.power, self.points_for[i], self.points_allowed[i]))
            
            
class Pythagenport:
    def __init__(self):
        self.teams = []
        self.points_allowed = []
        self.points_for = []
        self.win_loss_per = []
        self.power = []
        self.prediction = []
        
    
    def loadData(self, d):
        self.teams = d['teams']
        self.points_allowed = np.double(d['points_allowed'])
        self.points_for = np.double(d['points_for'])
        self.win_loss_per = np.double(d['wlp'])
        self.games = np.int(d['n_games'])

    
    def optimizeParams(self, vec):
        ssq = 0. 
        for i in range(len(self.teams)):
            x = vec[0] * np.log10((self.points_for[i]+self.points_allowed[i])*vec[1]/self.games)
            f = lambda pf, pa: pf**x/(pf**x + pa**x)
            calc = f(self.points_for[i], self.points_allowed[i])
            ssq += (self.win_loss_per[i] - calc)**2
        return ssq
        
        
    def calcPyth(self):
        guess = [1.5, 1.]
        self.xopt = fmin(self.optimizeParams, guess)
        for i in range(len(self.teams)):
            x = self.xopt[0] * np.log10((self.points_for[i]+self.points_allowed[i])*self.xopt[1]/self.games)
            f = lambda pf, pa: pf**x/(pf**x + pa**x)
            self.prediction.append(f(self.points_for[i], self.points_allowed[i]))
            self.power.append(x)
            

class Pythagenpat:
    def __init__(self):
        self.teams = []
        self.points_allowed = []
        self.points_for = []
        self.win_loss_per = []
        self.power = []
        self.prediction = []
        
    
    def loadData(self, d):
        self.teams = d['teams']
        self.points_allowed = np.double(d['points_allowed'])
        self.points_for = np.double(d['points_for'])
        self.win_loss_per = np.double(d['wlp'])
        self.games = np.int(d['n_games'])

    
    def optimizeParams(self, val):
        ssq = 0. 
        for i in range(len(self.teams)):
            x = ((self.points_for[i]+self.points_allowed[i])/self.games)**val
            f = lambda pf, pa: pf**x/(pf**x + pa**x)
            calc = f(self.points_for[i], self.points_allowed[i])
            ssq += (self.win_loss_per[i] - calc)**2
        return ssq
        
        
    def calcPyth(self):
        guess = 0.287
        self.xopt = fmin(self.optimizeParams, guess)[0]
        for i in range(len(self.teams)):
            x = ((self.points_for[i]+self.points_allowed[i])/self.games)**self.xopt
            f = lambda pf, pa: pf**x/(pf**x + pa**x)
            self.prediction.append(f(self.points_for[i], self.points_allowed[i]))
            self.power.append(x)
            
            
class Pythagorean(object):
    def __init__(self, dataDict):
        self.prediction = []
        self.power = []
        
        self.f = lambda pf, pa, x: pf**x / (pf**x + pa**x)
        self.guessedExp = 2.
	
	self.teams = dataDict['teams']
        self.points_for = np.double(dataDict['points_for'])
        self.points_against = np.double(dataDict['points_against'])
        self.wlp = np.double(dataDict['wlp'])
        self.ngames = np.int(dataDict['ngames'])
	
    
    def minimizeParameters(self, val):
        pass
    
       
    def calculatePythagorean(self):
        self.xopt = fmin(self.minimizeParameters, self.guessedExp)
        for i in range(len(self.teams)):
            self.prediction.append(self.f(self.points_for[i], self.points_against[i], self.xopt))
            self.power.append(self.xopt)
            

class PythExp(Pythagorean):
    def __init__(self, dataDict):
        super(PythExp, self).__init__(dataDict)

    def minimizeParameters(self, val):
        ssq = 0.
        for i in np.arange(0, len(self.teams)):
            calc = self.f(self.points_for[i], self.points_against[i], val)
            ssq += (self.wlp[i] - calc)**2
        return ssq
