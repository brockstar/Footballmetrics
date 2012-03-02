# IPython log file
import urllib2
import html5lib
import sqlite3 as sql

def getTeams(data_string):
    sign = data_string[6].split('</td')[0].split('>')[1].encode()

    t = lambda st: st.split('</a')[0].split('.htm">')[1].encode()

    if sign == '':
        home_team = t(data_string[5])
        away_team = t(data_string[7])
    elif sign == '@':
        home_team = t(data_string[7])
        away_team = t(data_string[5])
    else:
        #print 'ERROR when parsing for home and away teams.'
        #print 'Sign = %s' % sign
        home_team = away_team = ''

    return home_team, away_team


def getScores(data_string):
    sign = data_string[6].split('</td')[0].split('>')[1].encode()

    t = lambda st: st.split('</td')[0].split('"right">')[1].encode()

    sc1 = t(data_string[8])
    sc2 = t(data_string[9])
    if '<strong>' in sc1:
        sc1 = sc1.split('</st')[0].split('ong>')[1].encode()
    elif '<strong>' in sc2:
        sc2 = sc2.split('</st')[0].split('ong>')[1].encode()

    if sign == '':
        home_score = sc1
        away_score = sc2
    elif sign == '@':
        home_score = sc2
        away_score = sc1
    else:
        #print 'ERROR when parsing for home and away scores.'
        home_score = away_score = ''

    return home_score, away_score



url = 'http://www.pro-football-reference.com/years/2011/games.htm'
parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder('beautifulsoup'))
tree = parser.parse(urllib2.urlopen(url).read())
data = tree.findAll('tr')
data = data[1:]

games = []
j =  0
for i in data:
    decoded = str(i).decode('utf-8')
    s = decoded.strip().split('\n')
    s = [x.strip() for x in s]
    try:
        game = []
        week = s[1].split('</td')[0].split('">')[1].encode()
        home_team, away_team = getTeams(s)
        home_score, away_score = getScores(s)
        game += [week, home_team, away_team, int(home_score), int(away_score)]
        #print game
        games += [game]
    except:
        pass


con = sql.connect('nfl_games.db')
cur = con.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS games_2011 (Id INTEGER PRIMARY KEY AUTOINCREMENT, Week TEXT, HomeTeam TEXT, AwayTeam TEXT, HomeScore INTEGER, AwayScore INTEGER)')

for game in games:
    #print game
    cur.execute("INSERT INTO games_2011 VALUES(null,'%s','%s','%s','%d','%d')" % tuple(game))

con.commit()
con.close()
