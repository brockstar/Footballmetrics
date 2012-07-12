from __future__ import division

import sqlite3

class SOS(object):
    def __init__(self, team, year=None, week=None, db_path=None, db_table=None):
        self.team = team
        self.year = year
        self.week = week
        self.db_path = db_path
        self.db_table = db_table

    def calculate(self, method='average'):
        if method == 'average':
            self.__calc_avg()
        elif method == 'weighted_average':
            self.__calc_weighted_avg()
        elif method == 'bcs':
            return self.__calc_bcs()
        else:
            raise ValueError("Method %s doesn't exist." % method)

    def __calc_avg(self):
        print 'Not implemented yet.'

    def __calc_weighted_avg(self):
        print 'Not implemented yet.'

    def __calc_bcs(self):
        # Calculate W-L record of opponents
        opponents = self.__get_opponents(self.team)
        opponents_wins, opponents_total_games = self.__get_opponent_record(opponents)
        opponents_rec = opponents_wins / opponents_total_games
        # Calculate W-L record of opponent's opponents
        opp_opponents_wins = 0
        opp_opponents_total_games = 0
        for opp in opponents:
            temp_wins, temp_games = self.__get_opponent_record(self.__get_opponents(opp))
            opp_opponents_wins += temp_wins
            opp_opponents_total_games += temp_games
        opp_opponents_rec = opp_opponents_wins / opp_opponents_total_games
        sos = 2/3 * opponents_rec + 1/3 * opp_opponents_rec
        return sos
       
    def __get_opponents(self, team):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cmd = 'select %s from %s where Year=%d and Week<=%d and %s="%s"' % \
            ('HomeTeam', self.db_table, self.year, self.week, 'AwayTeam', team)
        cur.execute(cmd)
        opponents = [str(i[0]) for i in cur.fetchall()]
        cmd = 'select %s from %s where Year=%d and Week<=%d and %s="%s"' % \
            ('AwayTeam', self.db_table, self.year, self.week, 'HomeTeam', team)
        cur.execute(cmd)
        opponents += [str(i[0]) for i in cur.fetchall() if str(i[0]) not in opponents]
        con.close()
        return opponents

    def __get_opponent_record(self, teams):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        total_wins = 0
        total_games = 0
        for team in teams:
            cmd = 'select Win, Loss, Tie from standings where team="%s" and year=%d and week=%s' % (team, self.year, self.week)
            cur.execute(cmd)
            temp = cur.fetchall()[0]
            total_wins += temp[0] 
            total_games += sum(temp)
        con.close()
        return total_wins, total_games
