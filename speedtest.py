from __future__ import division
import timeit


# Preparation statement for timeit routine
tmp='''
import footballmetrics.dataloader as fm_dl
import footballmetrics.rankings as fm_rkg
import footballmetrics.pythagoreans as fm_pyth
games_df = fm_dl.from_sqlite('test.db', 'select * from games')
standings_df = fm_dl.from_sqlite('test.db', 'select * from standings')
pythag_df = fm_dl.from_sqlite('test.db', 'select * from pythagoreans')

fisb = fm_rkg.FISB_Ranking(games_df)
ml = fm_rkg.ML_Ranking(games_df, standings_df)
srs = fm_rkg.SRS(games_df, standings_df)
pyth = fm_pyth.PythagoreanExpectation(pythag_df)
port = fm_pyth.Pythagenport(pythag_df)
pat = fm_pyth.Pythagenpat(pythag_df)'''


print('{0:15}{1:>12}'.format('Method', 'Time [ms]'))
print('{0:15}{1:>12}'.format('-'*6, '-'*9))
# FISB, no bootstrapping
t1 = timeit.Timer('fisb.calculate_ranking()', tmp)
print('{0:15}{1:>12.3f}'.format('FISB', t1.timeit(1000)))
# FISB, with bootstrapping
t2 = timeit.Timer('fisb.calculate_ranking(1000)', tmp)
print('{0:15}{1:>12.3f}'.format('FISB bootstrap', t2.timeit(10) * 100))
# Max-L Ranking
t3 = timeit.Timer('ml.calculate_ranking()', tmp)
print('{0:15}{1:>12.3f}'.format('Max-L', t3.timeit(1000)))
# SRS
t4 = timeit.Timer('srs.calculate_ranking()', tmp)
print('{0:15}{1:>12.3f}'.format('SRS', t4.timeit(1000)))
# OSRS
t5 = timeit.Timer('srs.calculate_ranking(method="offense")', tmp)
print('{0:15}{1:>12.3f}'.format('OSRS', t5.timeit(1000)))
# DSRS
t6 = timeit.Timer('srs.calculate_ranking(method="defense")', tmp)
print('{0:15}{1:>12.3f}'.format('DSRS', t6.timeit(1000)))
# Pythagorean expectation
t7 = timeit.Timer('pyth.calculate_pythagorean()', tmp)
print('{0:15}{1:>12.3f}'.format('Pythagorean', t7.timeit(1000)))
# Pythagenport
t8 = timeit.Timer('port.calculate_pythagorean()', tmp)
print('{0:15}{1:>12.3f}'.format('Pythagenport', t8.timeit(1000)))
# Pythagenpat
t9 = timeit.Timer('pat.calculate_pythagorean()', tmp)
print('{0:15}{1:>12.3f}'.format('Pythagenpat', t9.timeit(1000)))

