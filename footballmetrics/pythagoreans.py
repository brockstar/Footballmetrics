from __future__ import division

import numpy as np
import scipy.optimize
import sqlite3


class Pythagorean(object):
    '''
    This is a super class for the different types of the 
    Pythagorean expectation. It is called with a dictionary containing 
    the teams, scores and number of played games (i.e. given week).

    * self.calculateExponent - Formula for the exponent x.
    * self.guess - Initial guess for the optimization
    '''
#    def __init__(self, dataDict):
#        self.teams = dataDict['teams']
#        self.pointsFor = np.double(dataDict['pointsFor'])
#        self.pointsAgainst = np.double(dataDict['pointsAgainst'])
#        self.wlp = np.double(dataDict['wlp'])
#        self.nGames = np.int(dataDict['nGames'])
	
    def __init__(self, year, week, db_path, db_table='standings'):
        self.prediction = {}
        self.power = {}
        self.__f = lambda pf, pa, x: pf**x / (pf**x + pa**x)
        self.calculateExponent = lambda pf, pa, x: x
        self.guess = 2.0
        self.__year = year
        self.__week = week
        self.__teams = []
        self.__pointsFor = []
        self.__pointsAgainst = []
        self.__wlp = []
        self.nGames = 0
        self.__load_data(db_path, db_table)

    def __load_data(self, db_path, db_table):
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cmd = 'select Team, PointsFor, PointsAgainst, Win, Loss, Tie from %s where Year=%d and Week=%d' % (db_table, self.__year, self.__week)
        cur.execute(cmd)
        tmp = cur.fetchall()
        con.close()
        for row in tmp:
            self.__teams.append(row[0])
            self.__pointsFor.append(row[1])
            self.__pointsAgainst.append(row[2])
            nGames, wlp = self.__get_wlp(row[3:])
            self.__wlp.append(wlp)
            self.nGames = nGames
        self.__pointsFor = np.double(self.__pointsFor)
        self.__pointsAgainst = np.double(self.__pointsAgainst)
        self.__wlp = np.double(self.__wlp)
        self.nGames = np.int(self.nGames)

    def getOptimalFitParams(self):
        '''
        Returns the optimal fit parameters retrieved from scipy.optimize.fmin 
        in calculatePythagorean().
        '''
        return self.__xopt

    def calculatePythagorean(self, optimize=True, staticParams=None):
        '''
        Returns the predictions and power for all given teams. 
        An optimatization for the exponent formula is performed, 
        if optimize is set to True. If set to False the static exponent 
        parameters need to be given as a list.
        '''
        if optimize:
            #best fit parameters
            self.__xopt = scipy.optimize.fmin(self.__minimizeParams, 
                                            self.guess)
        for i in range(len(self.__teams)):
            if optimize:
                #adjusted parameter per team
                x = self.calculateExponent(self.__pointsFor[i], 
                                           self.__pointsAgainst[i], 
                                           self.__xopt) 
            elif not optimize and staticParams != None:
                x = self.calculateExponent(self.__pointsFor[i], 
                                           self.__pointsAgainst[i], 
                                           staticParams)
            else:
                raise ValueError('No fit exponents given.')
            self.prediction[self.__teams[i]] = self.__f(self.__pointsFor[i], 
                                                        self.__pointsAgainst[i], 
                                                        x)
            self.power[self.__teams[i]] = x
        return self.prediction, self.power
        
    def __get_wlp(self, vals):
        games_played = sum(vals)
        wlp = vals[0] / games_played
        return games_played, wlp
        
    def __minimizeParams(self, val):
        ssq = 0.
        for i in np.arange(0, len(self.__teams)):
            x = self.calculateExponent(self.__pointsFor[i], 
                                       self.__pointsAgainst[i], val)
            calc = self.__f(self.__pointsFor[i], self.__pointsAgainst[i], x)
            ssq += (self.__wlp[i] - calc)**2
        return ssq


class PythagoreanExpectation(Pythagorean):
    '''
    Implementation of the classical Pythagorean expectation.
    '''
    def __init__(self, year, week, db_path, db_table='standings'):
        super(PythagoreanExpectation, self).__init__(year, week, db_path, db_table='standings')
        self.calculateExponent = lambda pf, pa, x: x[0]
        self.guess = 2.0

        
class Pythagenport(Pythagorean):
    '''
    Implementation of Clay Davenport's Pythagenport formula.
    '''
    def __init__(self, year, week, db_path, db_table='standings'):
        super(Pythagenport, self).__init__(year, week, db_path, db_table='standings')
        self.calculateExponent = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.nGames)+x[1]
        self.guess = [1.5, 0.45]
        

class PythagenportFO(Pythagorean):
    '''
    Implementation of Football Outsiders' Pythagenport formula.
    '''
    def __init__(self, year, week, db_path, db_table='standings'):
        super(PythagenportFO, self).__init__(year, week, db_path, db_table='standings')
        self.calculateExponent = lambda pf, pa, x: x[0]*np.log10((pf+pa)/self.nGames)
        self.guess = 1.5
        
        
class Pythagenpat(Pythagorean):
    '''
    Implementation of David Smyth's Pythagenpat formula.
    '''
    def __init__(self, year, week, db_path, db_table='standings'):
        super(Pythagenpat, self).__init__(year, week, db_path, db_table='standings')
        self.calculateExponent = lambda pf, pa, x: ((pf+pa)/float(self.nGames))**x[0]
        self.guess = 0.287
