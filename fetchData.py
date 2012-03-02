import urllib2
import html5lib
import sqlite3 as sql


class fetchGames:
    def __init__(self, years):
        self.years = list(years)
        
    def getSeasonGames(self):
        for year in self.years:
            print 'Processing %d season.' % (year)
            url = 'http://www.pro-football-reference.com/years/%s/games.htm' % (year)
            parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder('beautifulsoup'))
            tree = parser.parse(urllib2.urlopen(url).read())
            data = tree.findAll('tr')
            data = data[1:]
            
            games = []
            for i in data:
                decoded = str(i).decode('utf-8')
                s = decoded.strip().split('\n')
                s = [x.strip() for x in s]
                try:
                    game = []
                    week = s[1].split('</td')[0].split('">')[1].encode()
                    if week == 'Wildcard':
                        week = 18
                    elif week == 'Division':
                        week = 19
                    elif week == 'ConfChamp':
                        week = 20
                    elif week == 'SuperBowl':
                        week = 21
                    home_team, away_team = self.getTeamName(s)
                    home_score, away_score = self.getScore(s)
                    game += [int(year), int(week), home_team, away_team, int(home_score), int(away_score)]
                    games += [game]
                except:
                    pass
            
            print 'Writing data to database.'
            con = sql.connect('nfl_games.db')
            cur = con.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS games (Id INTEGER PRIMARY KEY AUTOINCREMENT, Year INTEGER, Week INTEGER, HomeTeam TEXT, AwayTeam TEXT, HomeScore INTEGER, AwayScore INTEGER)')
            
            for game in games:
                cur.execute("INSERT INTO games VALUES(null, %d, %d,'%s','%s','%d','%d')" % tuple(game))
            
            con.commit()
            con.close()
            print 'Done.'
    
        
    def getTeamName(self, data_string):
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


    def getScore(self, data_string):
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
    
    
class fetchStandings:
    def __init__(self, years):
        self.years = years

        
    def getStandings(self):
        con = sql.connect('nfl_games.db')
        cur = con.cursor()
        
        cur.execute('drop table if exists standings')
        cur.execute('create table standings(Id integer primary key autoincrement, Year int, Week int, Team text, Win int, Loss int, Tie int, PointFor int, PointsAgainst int)')
            
        for year in self.years:
            print 'Processing %d season.' % year
            t = []
            
            cur.execute('select HomeTeam, HomeScore from games where year=%d and week=1' % year)
            home = cur.fetchall()
            
            cur.execute('select AwayTeam, AwayScore from games where year=%d and week=1' % year)
            away = cur.fetchall()
            
            for h in home:
                t.append(h[0].encode())
            
            for a in away:
                t.append(a[0].encode())
            
            teams = dict.fromkeys(t)
            for t in teams.iterkeys():
                teams[t] = [0,0,0,0,0] # win, loss, tie, points for, points against
            
            cur.execute('select distinct week from games where year=%d' % year)
            weeks = [int(w[0]) for w in cur.fetchall()]
            
            for w in weeks:
                cur.execute('select * from games where year=%d and week=%d' % (year,w))
                result = cur.fetchall()
                for r in result:
                    # save points for and points againts for home team and away team
                    pts_home = [r[-2], r[-1]]
                    pts_away = [r[-1], r[-2]]
                    h = r[3].encode() # home team
                    a = r[4].encode() # away team
                    
                    if pts_home[0] > pts_home[1]:
                        teams[h] = [teams[h][0]+1, teams[h][1], teams[h][2], teams[h][3]+pts_home[0], teams[h][4]+pts_home[1]]
                    elif pts_home[0] < pts_home[1]:
                        teams[h] = [teams[h][0], teams[h][1]+1, teams[h][2], teams[h][3]+pts_home[0], teams[h][4]+pts_home[1]]
                    else:
                        teams[h] = [teams[h][0], teams[h][1], teams[h][2]+1, teams[h][3]+pts_home[0], teams[h][4]+pts_home[1]]
                    
                    if pts_away[0] > pts_away[1]:
                        teams[a] = [teams[a][0]+1, teams[a][1], teams[a][2], teams[a][3]+pts_away[0], teams[a][4]+pts_away[1]]
                    elif pts_away[0] < pts_away[1]:
                        teams[a] = [teams[a][0], teams[a][1]+1, teams[a][2], teams[a][3]+pts_away[0], teams[a][4]+pts_away[1]]
                    else:
                        teams[a] = [teams[a][0], teams[a][1], teams[a][2]+1, teams[a][3]+pts_away[0], teams[a][4]+pts_away[1]]
            
                for t in teams.iterkeys():
                    cur.execute('insert into standings values(null, %d, %d, "%s", %d, %d, %d,  %d, %d)' % (year, w,t,teams[t][0], teams[t][1], teams[t][2], teams[t][3], teams[t][4]))
                
        con.commit()
        
        con.close()