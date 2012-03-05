import footballmetrics.Pythagoreans as football_science
import sqlite3
import numpy as np
from scipy.stats import pearsonr

con = sqlite3.connect('nfl_games.db')
cur = con.cursor()

years = [2007,2008,2009,2010,2011]

w = 17

corr_pythagorean = []
corr_pythagenport = []
corr_pythagenpat = []

xopt_pythagorean = []
xopt_pythagenport = []
xopt_pythagenpat = []

pred_pythagorean = []
pred_pythagenport = []
pred_pythagenpat = []
wlp_array = []

for year in years:
    teams = []
    pa = []
    pf = []
    wlp = []
    wins = []

    print 'Season %d' % year
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

    pythagorean = football_science.PythagoreanExpectation(d, optimize=False)
    pythagorean.setStaticExp([2.37])
    pythagorean.calculatePythagorean()
    pythagenport = football_science.Pythagenport(d, optimize=False)
    pythagenport.setStaticExp([1.5, 0.45])
    pythagenport.calculatePythagorean()    
    pythagenpat = football_science.Pythagenpat(d, optimize=False)
    pythagenpat.setStaticExp([0.287])
    pythagenpat.calculatePythagorean()
    
    
    pred_pythagorean.append(dict(zip(teams,pythagorean.prediction)))
    pred_pythagenport.append(dict(zip(teams,pythagenport.prediction)))
    pred_pythagenpat.append(dict(zip(teams,pythagenpat.prediction)))
    wlp_array.append(dict(zip(teams,wlp)))
    
    corr_pythagorean.append(pearsonr(pythagorean.prediction, wlp))
    corr_pythagenport.append(pearsonr(pythagenport.prediction, wlp))
    corr_pythagenpat.append(pearsonr(pythagenpat.prediction, wlp))
    
    xopt_pythagorean.append(pythagorean.xopt)
    xopt_pythagenport.append(pythagenport.xopt)
    xopt_pythagenpat.append(pythagenpat.xopt)


for index, item in enumerate(years):    
    print '\nStatistics for %d season' % item
    print 'Pythagorean: p=%3.5f\txopt=%3.5f' % (corr_pythagorean[index][0], xopt_pythagorean[index][0])
    print 'Pythagenport: p=%3.5f\txopt=%3.5f %3.5f' % \
        (corr_pythagenport[index][0], xopt_pythagenport[index][0], xopt_pythagenport[index][1])
    print 'Pythagenpat: p=%3.5f\txopt=%3.5f' % (corr_pythagenpat[index][0], xopt_pythagenpat[index])

p_avg_pythagorean = np.average([x[0] for x in corr_pythagorean])
p_avg_pythagenport = np.average([x[0] for x in corr_pythagenport])
p_avg_pythagenpat = np.average([x[0] for x in corr_pythagenpat])

xopt1_avg = np.average([x[0] for x in xopt_pythagenport])
xopt2_avg = np.average([x[1] for x in xopt_pythagenport])

print '\nAverage from 2007-2011 season'
print 'Formula\t\t<p>\t<xopt>'
print 'Pythagorean:\t%3.5f\t%3.5f' % (p_avg_pythagorean, np.average(xopt_pythagorean))
print 'Pythagenport:\t%3.5f\t%3.5f %3.5f' % (p_avg_pythagenport, xopt1_avg, xopt2_avg)
print 'Pythagenpat:\t%3.5f\t%3.5f' % (p_avg_pythagenpat, np.average(xopt_pythagenpat))
