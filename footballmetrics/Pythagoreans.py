from __future__ import division
import numpy as np
from scipy.optimize import fmin


class Pythagorean(object):
    def __init__(self, dataDict):
        self.prediction = []
        self.power = []
        
        self.f = lambda pf, pa, x: pf**x / (pf**x + pa**x)
        self.exp = lambda pf, pa, x: x
        self.guessedExp = 2.0
        
        self.teams = dataDict['teams']
        self.points_for = np.double(dataDict['points_for'])
        self.points_against = np.double(dataDict['points_against'])
        self.wlp = np.double(dataDict['wlp'])
        self.ngames = np.int(dataDict['ngames'])
	
    
    def minimizeParameters(self, val):
        ssq = 0.
        for i in np.arange(0, len(self.teams)):
            x = self.exp(self.points_for[i], self.points_against[i], val)
            calc = self.f(self.points_for[i], self.points_against[i], x)
            ssq += (self.wlp[i] - calc)**2
        return ssq
    
       
    def calculatePythagorean(self):
        self.xopt = fmin(self.minimizeParameters, self.guessedExp)  #best fit parameters
        for i in range(len(self.teams)):
            x = self.exp(self.points_for[i], self.points_against[i], self.xopt) #adjusted parameter per team
            self.prediction.append(self.f(self.points_for[i], self.points_against[i], x))
            self.power.append(x)
            

class PythagoreanExpectation(Pythagorean):
    def __init__(self, dataDict):
        super(PythagoreanExpectation, self).__init__(dataDict)
        self.exp = lambda pf, pa, x: x[0]
        
    
class Pythagenport(Pythagorean):
    def __init__(self, dataDict):
        super(Pythagenport, self).__init__(dataDict)
        self.exp = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.ngames+x[1])
        self.guessedExp = [1.5, 0.45]
        
        
class Pythagenpat(Pythagorean):
    def __init__(self, dataDict):
        super(Pythagenpat, self).__init__(dataDict)
        self.exp = lambda pf, pa, x: ((pf+pa)/self.ngames)**x[0]
        self.guessedExp = 0.287
