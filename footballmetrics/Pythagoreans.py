from __future__ import division
import numpy as np
import scipy.optimize


class Pythagorean(object):
    '''
    This is a super class for the different types of the Pythagorean expectation.
    It is called with a dictionary containing the teams, scores and number of played games (i.e. given week).

    * self.f - The general formula for each Pythagorean Expectation.
    * self.exp - The formula for the exponent.
    * self.guess - Initial guess for the optimization
    '''
    def __init__(self, dataDict):
        self.prediction = []
        self.power = []
        
        self.f = lambda pf, pa, x: pf**x / (pf**x + pa**x)
        self.calculateExponent = lambda pf, pa, x: x
        self.guess = 2.0
        
        self.teams = dataDict['teams']
        self.pointsFor = np.double(dataDict['points_for'])
        self.pointsAgainst = np.double(dataDict['points_against'])
        self.wlp = np.double(dataDict['wlp'])
        self.nGames = np.int(dataDict['ngames'])
	

    def getOptimalFitParams(self):
        try:
            return self.xopt
        except:
            print 'ERROR. There was no optimazation performed.'
 
    
    def minimizeParams(self, val):
        '''
        Helper function to minimize the function self.f with the given parameters.
        '''
        ssq = 0.
        for i in np.arange(0, len(self.teams)):
            x = self.calculateExponent(self.pointsFor[i], self.pointsAgainst[i], val)
            calc = self.f(self.pointsFor[i], self.pointsAgainst[i], x)
            ssq += (self.wlp[i] - calc)**2
        return ssq
    
       
    def calculatePythagorean(self, optimize=True, staticParams=None):
        '''
        The main routine that calculates the predictions and the power of the Pythagorean expectation.
        Uses the scipy.optimize.fmin method to minimize the helper function given in minimizeParameters()
        '''
        try:
            if optimize:
                self.xopt = scipy.optimize.fmin(self.minimizeParams, self.guess)  #best fit parameters

            for i in range(len(self.teams)):
                if optimize:
                    x = self.calculateExponent(self.pointsFor[i], self.pointsAgainst[i], self.xopt) #adjusted parameter per team
                elif not optimize and staticParams != None:
                    x = self.calculateExponent(self.pointsFor[i], self.pointsAgainst[i], staticParams)
                else:
                    print 'ERROR. There were no static parameters given, ',
                    print 'albeit method was called without optimization.'
                
                self.prediction.append(self.f(self.pointsFor[i], self.pointsAgainst[i], x))
                self.power.append(x)
                
            return self.prediction, self.power
        
        except:
            raise
            


class PythagoreanExpectation(Pythagorean):
    '''
    Implementation of the "classical" Pythagorean expectation.
    '''
    def __init__(self, dataDict, optimize=True):
        super(PythagoreanExpectation, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: x[0]
        
    
    
class Pythagenport(Pythagorean):
    '''
    Implementation of the Pythagenport formula.
    The exponent is calculated as (x0 * log10((pf+pa)/nGames) + x1). Traditionally, x0 = 1.5 and x1 = 0.45.
    '''
    def __init__(self, dataDict, optimize=True):
        super(Pythagenport, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.nGames+x[1])
        self.guess = [1.5, 0.45]
        
        
        
class Pythagenpat(Pythagorean):
    '''
    Implementation of the Pythagenpat formula.
    The exponent is calculated as ((pf+pa)/nGames)**x. Traditionally, x = 0.287.
    '''
    def __init__(self, dataDict, optimize=True):
        super(Pythagenpat, self).__init__(dataDict)
        self.calculateExponent = lambda pf, pa, x: ((pf+pa)/self.nGames)**x[0]
        self.guess = 0.287
