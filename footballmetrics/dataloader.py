from __future__ import division

import os
import sqlite3

import numpy as np
import pandas as pd
import pandas.io.sql as pd_sql


class DataLoader(object):
    def __init__(self):
        pass

    def load_sqlite(self, db_path, query):
        if not os.path.isfile(db_path):
            raise IOError('Database does not exist.')
        con = sqlite3.connect(db_path)
        self.df = pd_sql.read_frame(query, con)
        con.close()
        return self.df

    def load_csv(self, filename):
        if not os.path.isfile(filename):
            raise IOError('File not found.')
        self.df = pd.read_csv(filename)
        return self.df
