from __future__ import division

import numpy as np
import scipy.optimize as sc_opt

import footballmetrics.dataloader as fm_dl


def get_pythag(pts_for, pts_against, x=2.63):
    '''
    Returns Pythagorean expectation (PE) for given values.
    This is merely a convenience function for quick calculations.
    '''
    pyth = lambda pf, pa, x: pf ** x / (pf ** x + pa ** x)
    return pyth(pts_for, pts_against, x)


class PythagoreanExpectation(object):
    def __init__(self, standings_df):
        self._standings = standings_df
        self._dh = fm_dl.DataHandler(standings_df=standings_df)
        self._params = [2.63]
    
    def _pyth(self, pf, pa, x): 
        return pf ** x / (pf ** x + pa ** x)
   
    def set_exponent(self, val):
        '''If you don't want to optimize the exponent, you can set its value here.'''
        if not type(val) in [list, np.ndarray]:
            self._params = np.array([val])
        else:
            self._params = np.array(val)

    def get_exponent(self):
        return self._params

    def calculate_pythagorean(self, optimize=True):
        pts_for = self._standings['PointsFor']
        pts_against = self._standings['PointsAgainst']
        if optimize:
            # Set optimized _params by calling _optimize()
            self._optimize(pts_for, pts_against)
        pythagoreans = self._pyth(pts_for, pts_against, self._params)
        return pythagoreans

    def _optimize(self, pf, pa):
        wlp = self._dh.get_wins() / self._dh.get_number_of_games()
        errfunc = lambda x, pf, pa: self._pyth(pf, pa, x) - wlp
        xopt, success = sc_opt.leastsq(errfunc, x0=self._params, args=(pf, pa))
        self._params = xopt


class Pythagenpat(PythagoreanExpectation):
    def __init__(self, standings_df):
        super(Pythagenpat, self).__init__(standings_df)
        self._params = [0.287]
        self._n_games = self._dh.get_number_of_games()
        self._exp = lambda pf, pa, x: ((pf + pa) / self._n_games) ** x

    def _pyth(self, pf, pa, x):
        p = pf ** self._exp(pf, pa, x) / (pf ** self._exp(pf, pa, x) + pa ** self._exp(pf, pa, x))
        return p


class Pythagenport(Pythagenpat):
    def __init__(self, standings_df):
        super(Pythagenport, self).__init__(standings_df)
        self._params = [1.45, 0.45]
        self._exp = lambda pf, pa, x: x[0] * np.log10((pf + pa) / self._n_games) + x[1]
 
