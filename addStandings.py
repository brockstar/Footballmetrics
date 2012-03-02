import sqlite3 as sql

con = sql.connect('nfl_games.db')
cur = con.cursor()

for year in years:
    print 'Processing %d season.' % year
    t = []
    
    cur.execute('select HomeTeam, HomeScore from games where year=%d and week=1' % year)
    home = cur.fetchall()
    
    cur.execute('select AwayTeam, AwayScore from games_2011 where year=%d and week=1' % year)
    away = cur.fetchall()
    
    for h in home:
        t.append(h[0].encode())
    
    for a in away:
        t.append(a[0].encode())
    
    teams = dict.fromkeys(t)
    for t in teams.iterkeys():
        teams[t] = [0,0,0,0,0] # win, loss, tie, points for, points against
    
    cur.execute('select distinct week from games')
    weeks = [int(w[0]) for w in cur.fetchall()]
    
    cur.execute('drop table if exists standings')
    cur.execute('create table standings_2011(Id integer primary key autoincrement, Year int, Week int, Team text, Win int, Loss int, Tie int, PointFor int, PointsAgainst int)')
    
    for w in weeks:
        cur.execute('select * from games where year=%d and week=%d' % (year,w))
        result = cur.fetchall()
        for r in result:
            # save points for and points againts for home team and away team
            pts_home = [r[-2], r[-1]]
            pts_away = [r[-1], r[-2]]
            h = r[2].encode() # home team
            a = r[3].encode() # away team
            
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
