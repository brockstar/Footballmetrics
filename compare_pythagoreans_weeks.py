import footballmetrics.Pythagoreans as football_science
import sqlite3
import numpy as np
from scipy.stats import pearsonr

con = sqlite3.connect('nfl_games.db')
cur = con.cursor()

years = [2007,2008,2009,2010,2011]

weeks = np.arange(2,18)

exp_pythagorean = []
exp_pythagenport = []
exp_pythagenpat = []

for year in years:
    for w in weeks:
        teams = []
        pa = []
        pf = []
        wlp = []
        wins = []
    
        print 'Season %d Week %d' % (year, w)
        cur.execute('select * from standings where year=%d and week=%d' % (year, w))
        results = cur.fetchall()
        cur.execute('select count(*) from standings where year=%d and week=%d' % (year, w))
        
        for row in results:
            teams.append(row[3].encode())
            pf.append(row[-2])
            pa.append(row[-1])
            x = row[4] / float(row[4]+row[5]+row[6])
            wlp.append(x)
            wins.append(row[4])
        
        d = {'teams':teams, 'points_against':pa, 'points_for':pf, 'wlp':wlp, 'ngames':w}
    
        pythagorean = football_science.PythagoreanExpectation(d)
        pythagorean.calculatePythagorean()
        pythagenport = football_science.Pythagenport(d)
        pythagenport.calculatePythagorean()    
        pythagenpat = football_science.Pythagenpat(d)
        pythagenpat.calculatePythagorean()
        
        exp_pythagorean.append(pythagorean.power[0])
        exp_pythagenport.append(pythagenport.power)
        exp_pythagenpat.append(pythagenpat.power)