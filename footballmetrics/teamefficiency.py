from __future__ import division

import numpy as np
import pandas as pd
import statsmodels.api as sm

class OffenseEfficiency(object):
    def __init__(self, train_data_path=None):
        '''
        The OffenseEfficiency class creates a score based on
        net yards per pass attempt, interception rate, yards per rush attempt
        and lost fumble rate.
        Also a separation in pass and rush scores is possible.
        '''
        self.__train(train_data_path)

    def __load_predictors(self, data):
        predictors = sm.add_constant(np.column_stack((data['NY/A'],
                                                      data['Int'] / data['PassAtt'],
                                                      data['RushYds'] / data['RushAtt'],
            data['FL'] / (data['RushAtt'] + data['PassAtt']))))
        return predictors
    def __train(self, train_data_path):
        if train_data_path is not None:
            try:
                data = pd.read_csv(train_data_path, index_col='Tm')
            except IOError, e:
                print('IOError: %s' % e)
        else:
            data = pd.read_csv('../off_team_efficiency.csv', index_col='Tm')
        data['intercept'] = 1.0
        X = self.__load_predictors(data)
        Y = data['Pts'] / data['G']
        model = sm.OLS(Y, X)
        self.__fit = model.fit()
        print('Model successfully created.')

    def predict(self, data, pred_type='full', norm=False, ret='pd'):
        '''
        Predicts efficiency for *data*.
        *pred_type* = {'full', 'pass', 'rush'}
        If *norm* = True, results will be normalized to mean = 0.
        *ret* = {'pd', 'np'} determines if pandas object
        or NumPy array will be returned.
        '''
        data = pd.DataFrame(data)
        Xpred = self.__load_predictors(data)
        params = self.__fit.params
        if pred_type == 'full':
            Ypred = self.__fit.predict(Xpred)
        elif pred_type == 'pass':
            pred_pass = lambda x: params[0] * x[:, 0] + params[1] * x[:, 1]
            Ypred = pred_pass(Xpred)
        elif pred_type == 'rush':
            pred_rush = lambda x: params[2] * x[:, 2] + params[3] * x[:, 3]
            Ypred = pred_rush(Xpred)
        if norm:
            Ypred -= Ypred.mean()
        s = 'Prediction_Off'
        if pred_type == 'pass' or pred_type == 'rush':
            s += '_' + pred_type
        data[s] = Ypred
        if ret == 'pd':
            return_data = data
        elif ret == 'np':
            return_data = Ypred
        return return_data


class DefenseEfficiency(object):
    def __init__(self, train_data_path=None):
        '''
        The DefenseEfficiency class creates a score based on
        net yards per pass attempt, interception rate and yards per rush attempt.
        '''
        self.__train(train_data_path)

    def __load_predictors(self, data):
        predictors = sm.add_constant(np.column_stack((data['NY/A'],
                                                      data['Int'] / data['PassAtt'],
                                                      data['RushYds'] / data['RushAtt'])))
        return predictors
    def __train(self, train_data_path):
        if train_data_path is not None:
            try:
                data = pd.read_csv(train_data_path, index_col='Tm')
            except IOError, e:
                print('IOError: %s' % e)
        else:
            try:
                data = pd.read_csv('../def_team_efficiency.csv', index_col='Tm')
            except IOError, e:
                print('IOError: %s' % e)
        data['intercept'] = 1.0
        X = self.__load_predictors(data)
        Y = data['Pts'] / data['G']
        model = sm.OLS(Y, X)
        self.__fit = model.fit()
        print('Model successfully created.')

    def predict(self, data, norm=False, ret='pd'):
        '''
        Predicts efficiency for *data*.
        If *norm* = True, results will be normalized to mean = 0.
        *ret* = {'pd', 'np'} determines if pandas object
        or NumPy array will be returned.
        '''
        data = pd.DataFrame(data)
        Xpred = self.__load_predictors(data)
        Ypred = self.__fit.predict(Xpred)
        if norm:
            Ypred -= Ypred.mean()
        data['Prediction_Def'] = Ypred
        if ret == 'pd':
            return_data = data
        elif ret == 'np':
            return_data = Ypred
        return return_data
