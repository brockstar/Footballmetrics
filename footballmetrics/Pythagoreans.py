from __future__ import division
import numpy as np
from scipy.optimize import fmin


class Pythagorean(object):
    '''
    This is a super class for the different types of the Pythagorean expectation.
    It is called with a dictionary containing the teams, scores and number of played games (i.e. given week).

    * self.f - The general formula for each Pythagorean Expectation.
    * self.exp - The formula for the exponent.
    * self.guessedExp - Initial guess for the optimization
    '''
    def __init__(self, dataDict, optimize=True):
        self.prediction = []
        self.power = []
        self.optimize = optimize
        
        self.f = lambda pf, pa, x: pf**x / (pf**x + pa**x)
        self.exp = lambda pf, pa, x: x
        self.guessedExp = 2.0
        
        self.teams = dataDict['teams']
        self.points_for = np.double(dataDict['points_for'])
        self.points_against = np.double(dataDict['points_against'])
        self.wlp = np.double(dataDict['wlp'])
        self.ngames = np.int(dataDict['ngames'])
	

    def setStaticExp(self, val):
        if not self.optimize:
            self.staticExp = val
        else:
            print 'ERROR. Setting static exponents is only allowed when initialized with no optimization.'

    
    def minimizeParameters(self, val):
        '''
        Helper function to minimize the function self.f with the given parameters.
        '''
        ssq = 0.
        for i in np.arange(0, len(self.teams)):
            x = self.exp(self.points_for[i], self.points_against[i], val)
            calc = self.f(self.points_for[i], self.points_against[i], x)
            ssq += (self.wlp[i] - calc)**2
        return ssq
    
       
    def calculatePythagorean(self):
        '''
        The main routine that calculates the predictions and the power of the Pythagorean expectation.
        Uses the scipy.optimize.fmin method to minimize the helper function given in minimizeParameters()
        '''
        #if self.optimize:
        self.xopt = fmin(self.minimizeParameters, self.guessedExp)  #best fit parameters

        for i in range(len(self.teams)):
            if self.optimize:
                x = self.exp(self.points_for[i], self.points_against[i], self.xopt) #adjusted parameter per team
            else:
                x = self.exp(self.points_for[i], self.points_against[i], self.staticExp)
            self.prediction.append(self.f(self.points_for[i], self.points_against[i], x))
            self.power.append(x)
            

class PythagoreanExpectation(Pythagorean):
    '''
    Implementation of the "classical" Pythagorean expectation.
    '''
    def __init__(self, dataDict, optimize=True):
        super(PythagoreanExpectation, self).__init__(dataDict, optimize)
        self.exp = lambda pf, pa, x: x[0]
        
    
class Pythagenport(Pythagorean):
    '''
    Implementation of the Pythagenport formula.
    The exponent is calculated as (x0 * log10((pf+pa)/ngames) + x1). Traditionally, x0 = 1.5 and x1 = 0.45.
    '''
    def __init__(self, dataDict, optimize=True):
        super(Pythagenport, self).__init__(dataDict, optimize)
        self.exp = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.ngames+x[1])
        self.guessedExp = [1.5, 0.45]
        
        
class Pythagenpat(Pythagorean):
    '''
    Implementation of the Pythagenpat formula.
    The exponent is calculated as ((pf+pa)/ngames)**x. Traditionally, x = 0.287.
    '''
    def __init__(self, dataDict, optimize=True):
        super(Pythagenpat, self).__init__(dataDict, optimize)
        self.exp = lambda pf, pa, x: ((pf+pa)/self.ngames)**x[0]
        self.guessedExp = 0.287
