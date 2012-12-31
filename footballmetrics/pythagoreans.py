from __future__ import division

import numpy as np
import scipy.optimize as sc_opt

import footballmetrics.dataloader as fm_dl


def get_pythag(pts_for, pts_against, x=2.63, **kwargs):
    '''
    Returns Pythagorean expectation (PE).
    This is merely a convenience function for quick calculations.

    Parameters
    ----------
    pts_for : int
        Points made by team.
    pts_against : int
        Points suffered by team (= points made by team's opponents).
    x : float
        Exponent of PE.

    kwargs
    ------
    func : callable
        Custom function for calculation of PE.
        Needs to accept 3 parameters: pts_for, pts_against, x

    Returns
    -------
    pyth : float
        Pythagorean expectation = predicted win percentage.
    '''
    if 'func' in kwargs:
        pyth = kwargs['func']
    else:
        pyth = lambda pf, pa, x: pf ** x / (pf ** x + pa ** x)
    return pyth(pts_for, pts_against, x)


class PythagoreanExpectation(object):
    def __init__(self, standings_df):
        '''
        This class is an implementation of the Pythagorean Expectation (PE).
        The PE calculates a value that is commonly interpreted as the number of wins
        a team should have based on points made and points suffered.
        The formula for PE is simply:
        Win_percentage = PF ** x / (PF ** x + PA ** x)
        x = 2.63 by default.

        Parameters
        ----------
        standings_df : pandas Data Frame, footballmetrics.DataLoader
                DataFrame or DataLoader object containing the standings, 
                for which the PE shall be calculated.
                Needs to have columns [Win, Loss, Tie, PointsFor, PointsAgainst].
        '''
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
        '''
        Returns the exponent x of PE. If an optimization was performed before calling
        this function, the optimized exponent will be returned.
        '''
        return self._params

    def calculate_pythagorean(self, optimize=True):
        '''
        Calculates the Pythagorean expectation. 
        
        Parameters
        -----------
        optimize : bool
                If True an optimization will be performed, otherwise a preset value
                will be used.

        Returns
        -------
        pythagoreans : pandas Series
                This will be a pandas Series containing the calculated 
                Pythagorean expecations with team names as index.

        See also
        --------
        PythagoreanExpectation.set_exponent
        PythagoreanExpectation.get_exponent
        '''
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
        if 1 <= success <= 4:
            self._params = xopt
        else:
            raise ValueError('Optimization did terminate successfully.')


class Pythagenpat(PythagoreanExpectation):
    def __init__(self, standings_df):
        '''
        This class is an implementation of Pythagenpat.
        Pythagenpat uses the same formula as Pythagorean Expectation for 
        calculating the expected win percentage, but contrary to PE it has no
        static exponent.
        The exponent is defined as follows:
        x = ((PF + PA) / (# of games)) ** z
        z = 0.287 by default.

        Parameters
        ----------
        standings_df : pandas Data Frame, footballmetrics.DataLoader
                DataFrame or DataLoader object containing the standings, 
                for which the PE shall be calculated.
                Needs to have columns [Win, Loss, Tie, PointsFor, PointsAgainst].

        See also
        --------
        PythagoreanExpectation : super class of Pythagenpat
        '''
        super(Pythagenpat, self).__init__(standings_df)
        self._params = [0.287]
        self._n_games = self._dh.get_number_of_games()
        self._exp = lambda pf, pa, x: ((pf + pa) / self._n_games) ** x

    def _pyth(self, pf, pa, x):
        exp = self._exp
        p = pf ** exp(pf, pa, x) / (pf ** exp(pf, pa, x) + pa ** exp(pf, pa, x))
        return p


class Pythagenport(Pythagenpat):
    def __init__(self, standings_df):
        '''
        This class is an implementation of Pythagenport.
        Pythagenport uses the same formula as Pythagorean Expectation for 
        calculating the expected win percentage, but similar to Pythagenpat
        it has no static exponent.
        The exponent is defined as follows:
        x = z1 * log10((PF + PA) / (# of games)) + z2
        By default:
            z1 = 1.45
            z2 = 0.45

        Parameters
        ----------
        standings_df : pandas Data Frame, footballmetrics.DataLoader
                       DataFrame or DataLoader object containing the standings, 
                       for which the PE shall be calculated.
                       Needs to have following columns: 
                            [Win, Loss, Tie, PointsFor, PointsAgainst].

        See also
        --------
        Pythagenpat, PythagoreanExpectation : super class of Pythagenpat
        '''
        super(Pythagenport, self).__init__(standings_df)
        self._params = [1.45, 0.45]
        self._exp = lambda pf, pa, x: x[0] * np.log10((pf + pa) / self._n_games) + x[1]
 
