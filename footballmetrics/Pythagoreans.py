from __future__ import division
import numpy as np
import scipy.optimize


class Pythagorean(object):
    '''
    This is a super class for the different types of the 
    Pythagorean expectation. It is called with a dictionary containing 
    the teams, scores and number of played games (i.e. given week).

    * self.calculateExponent - Formula for the exponent x.
    * self.guess - Initial guess for the optimization
    '''
    def __init__(self, dataDict):
        self.prediction = []
        self.power = []
        
        self.f = lambda pf, pa, x: pf**x / (pf**x + pa**x)
        self.calculateExponent = lambda pf, pa, x: x
        self.guess = 2.0
        
        self.teams = dataDict['teams']
        self.pointsFor = np.double(dataDict['pointsFor'])
        self.pointsAgainst = np.double(dataDict['pointsAgainst'])
        self.wlp = np.double(dataDict['wlp'])
        self.nGames = np.int(dataDict['nGames'])
	
    def getOptimalFitParams(self):
        '''
        Returns the optimal fit parameters retrieved from scipy.optimize.fmin 
        in calculatePythagorean().
        '''
        try:
            return self.xopt
        except:
            raise
        
    def __minimizeParams(self, val):
        ssq = 0.
        for i in np.arange(0, len(self.teams)):
            x = self.calculateExponent(self.pointsFor[i], 
                                       self.pointsAgainst[i], val)
            calc = self.f(self.pointsFor[i], self.pointsAgainst[i], x)
            ssq += (self.wlp[i] - calc)**2
        return ssq
    
    def calculatePythagorean(self, optimize=True, staticParams=None):
        '''
        Returns the predictions and power for all given teams. 
        An optimatization for the exponent formula is performed, 
        if optimize is set to True. If set to False the static exponent 
        parameters need to be given as a list.
        '''
        try:
            if optimize:
                self.xopt = scipy.optimize.fmin(self.__minimizeParams, self.guess)  #best fit parameters

            for i in range(len(self.teams)):
                if optimize:
                    x = self.calculateExponent(self.pointsFor[i], 
                                               self.pointsAgainst[i], self.xopt) #adjusted parameter per team
                elif not optimize and staticParams != None:
                    x = self.calculateExponent(self.pointsFor[i], 
                                               self.pointsAgainst[i], staticParams)
                else:
                    x = None
                
                self.prediction.append(self.f(self.pointsFor[i], 
                                              self.pointsAgainst[i], x))
                self.power.append(x)
                
            return self.prediction, self.power
        except:
            raise
        

class PythagoreanExpectation(Pythagorean):
    '''
    Implementation of the classical Pythagorean expectation.
    '''
    def __init__(self, dataDict):
        super(PythagoreanExpectation, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: x[0]
        
class Pythagenport(Pythagorean):
    '''
    Implementation of Clay Davenport's Pythagenport formula.
    '''
    def __init__(self, dataDict):
        super(Pythagenport, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.nGames)+x[1]
        self.guess = [1.5, 0.45]
        

class PythagenportFO(Pythagorean):
    '''
    Implementation of Football Outsiders' Pythagenport formula.
    '''
    def __init__(self, dataDict):
        super(PythagenportFO, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.nGames)
        self.guess = 1.5
        
        
class Pythagenpat(Pythagorean):
    '''
    Implementation of David Smyth's Pythagenpat formula.
    '''
    def __init__(self, dataDict):
        super(Pythagenpat, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: ((pf+pa)/float(self.nGames))**x[0]
        self.guess = 0.287
