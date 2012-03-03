from __future__ import division
import numpy as np
from scipy.optimize import fmin


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
        ssq = 0.
        for i in np.arange(0, len(self.teams)):
            calc = self.f(self.points_for[i], self.points_against[i], val)
            ssq += (self.wlp[i] - calc)**2
        return ssq
    
       
    def calculatePythagorean(self):
        self.xopt = fmin(self.minimizeParameters, self.guessedExp)
        for i in range(len(self.teams)):
            self.prediction.append(self.f(self.points_for[i], self.points_against[i], self.xopt))
            self.power.append(self.xopt)
            

class PythagoreanExpectation(Pythagorean):
    def __init__(self, dataDict):
        super(PythagoreanExpectation, self).__init__(dataDict)
        
    
class Pythagenport(Pythagorean):
    def __init__(self, dataDict):
        super(Pythagenport, self).__init__(dataDict)
        self.f = lambda pf, pa, x: pf**(x[0]*np.log10((pf+pa)/self.ngames+x[1])) \
            / (pf**(x[0]*np.log10((pf+pa)/self.ngames+x[1])) + pa**(x[0]*np.log10((pf+pa)/self.ngames+x[1])))
        self.guessedExp = [1.5, 0.45]
        
        
class Pythagenpat(Pythagorean):
    def __init__(self, dataDict):
        super(Pythagenpat, self).__init__(dataDict)
        self.f = lambda pf, pa, x: pf**(((pf+pa)/self.ngames)**x) \
            / (pf**(((pf+pa)/self.ngames)**x) + pa**(((pf+pa)/self.ngames)**x))
        self.guessedExp = 0.287
