import os

import sqlite3


class DraftValue:
    '''
    This class uses the draft value chart to calculate the value of a pick
    at a certain position or to calculate the corresponding draft position
    of a given value.
    '''
    def __init__(self):
        self.db_path = '../draft_value_chart.db'
    
    def get_value(self, position):
        '''Returns the value of a pick at the given *position*.'''
        if not os.path.isfile(self.db_path):
            raise IOError('Database not found. Please use set_database_path.')
        con = sqlite3.connect(self.db_path)
        with con:
            cur = con.cursor()
            try:
                cur.execute('select value from draft_value where position=%d'
                             % position)
            except TypeError:
                raise TypeError('Position needs to be an integer number.')
            value = cur.fetchone()[0]
        return value

    def get_position(self,value):
        '''Returns the draft pick for a given *value*.'''
        con = sqlite3.connect(self.db_path)
        with con:
            cur = con.cursor()
            try:
                cur.execute('select position from draft_value where value<=%f'
                             % value)
            except TypeError:
                raise TypeError('Value needs to be a number.')
            position = cur.fetchone()[0]
        return position
    
    def set_database_path(self, path):
        '''
        Use this method to set the path to the database, if it defers
        from default.
        '''
        if os.path.isfile(path):
            self.db_path = path
        else:
            raise IOError('File not found.')


if __name__ == '__main__':
    d = DraftValue()
    print 2*d.get_value(32) + d.get_value(38) + d.get_value(6)
    print d.get_position(294)