# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 23:35:33 2018

@author: Navya
"""
import geopy
import csv
import itertools
import pandas as pd
import pandas.io.sql as pd_sql
import sqlite3
from gurobipy import *
#%%To get the Game variables
#gamevar={}
#with open("GameVariables_2018.csv", "r") as myCSV:
#    myReader = csv.reader(myCSV)
#    for row in myReader:
#        gamevar[row[0], row[1], row[2], row[3], row[4]] = (float(row[5]))
gamevar={}
with open("GameVariables_2018.csv", "r") as myCSV:
    lines = itertools.islice(myCSV, 1, None)
    myReader = csv.reader(lines)
    for row in myReader:
        gamevar[row[0], row[1], row[2], row[3], row[4]] = (float(row[5]))
#%%To get the Away and Home data
away = {}
home = {}
team = []

for a,h,w,s,n in gamevar:
    if a not in away:
        away[a] = []
    if h not in away[a]:
        away[a].append(h)
    if h not in home and h != 'BYE':        
        home[h] = []
    if h != 'BYE':
        if a not in home[h]:
            home[h].append(a)
    if a not in team:
        team.append(a)
#%%To get the conferences and divisions
conf = {}  
div = {}      
with open("TEAM_DATA_2018.csv", "r") as myCSV:
    lines = itertools.islice(myCSV, 1, None)
    myReader = csv.reader(lines)      
    for row in myReader:
        if row[1] not in conf:
            conf[row[1]] = []
        conf[row[1]].append(row[0])
        if row[1] not in div:
            div[row[1]] = {}
        if row[2] not in div[row[1]]:
            div[row[1]][row[2]]= []
        div[row[1]][row[2]].append(row[0])  
#%%To get team data
teamdata= pd.read_csv("TEAM_DATA_2018.csv")
#%%To get game variables
gamedata= pd.read_csv("GameVariables_2018.csv")           
#%%To get the Game list
gamelist=[]
for a,h,w,s,n in gamevar:
    gamelist.append((a,h,w,s,n))
gamelist = tuplelist(gamelist)
#%%Create the model
nfl = Model()
nfl.modelSense = GRB.MAXIMIZE
nfl.update()        
#%%create the matchups
games = {}
for a,h,w,s,n in gamevar:
    OName = 'games_played_%s_%s_%s_%s_%s' % (a,h,w,s,n)
    games[a,h,w,s,n] = nfl.addVar(obj = gamevar[a,h,w,s,n], 
                                  vtype = GRB.BINARY, 
                                  name = OName)
nfl.update()
#%%Every matchup will be played only once
myConstrs = {}
for t in team:
        for h in away[t]:
            CName = '01_Each_game_once_%s_%s' % (t,h)
            myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,h,'*','*','*')) == 1,
                     name = CName)
nfl.update()
#%%Every team will play once a week
for t in team:
    for w in range(1,18):
        CName = '02_Each_team_once_%s_%s' % (t,w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',str(w),'*','*')) + 
                 quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,str(w),'*','*')) == 1, name = CName)
nfl.update()
#%%Byes can only happen between weeks 4 and 11
for t in team:
    for w in range(1,18):
        CName = '03_Bye_only_once_%s_%s' % (t,w)
        if (w in range (4,12)):
            myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n, in gamelist.select(t,'BYE',str(w),'*','*')) <= 1,
            name = CName)
        else:
            myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n, in gamelist.select(t,'BYE',str(w),'*','*')) == 0,
            name = CName)
nfl.update()
#%%No more than 6 byes in a given a week 
for w in range(4,12):
    CName = '04_Nomorethan6_Bye_week_%s'% w
    myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','BYE',str(w),'SUNB','BYE')) <= 6,
                                         name = CName)    
nfl.update()
#%%No team that had an early bye (week 4) in 2017 can have an early bye game (week 4) in 2018 
for t in team:
    for w in range (4,12):
        CName = '05_No_early_byes_%s_%s' % (t,w)
        if((t=="MIA" or t=="TB") and w==4):
            myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'BYE',str(w),'SUNB','BYE')) == 0,
                                         name = CName)         
nfl.update()
#%%There is one Thursday Night Game per week for weeks 1 through 16 (no Thursday Night Game in week 17) 
for w in range (1,18):
    CName = '06_One_game_THUN_%s' % (w)    
    if(w in range(1,17)):
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'THUN','*')) == 1,
                                     name = CName)
    else:
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'THUN','*')) == 0,
                                     name = CName)
nfl.update()
#%%There are two Saturday Night Games in Week 16 (one SatE and one SatL)
for w in range (1,18):
    if(w == 16):
        CName = '07a_games_SATL_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SATL','*')) == 1,
                                     name = CName)
        CName = '07a_games_SATE_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SATE','*')) == 1,
                                     name = CName)
    else:
        CName = '07b_games_SATL_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SATL','*')) == 0,
                                     name = CName)
        CName = '07b_games_SATE_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SATE','*')) == 0,
                                     name = CName)
nfl.update()
#%%There is only one “double header” game in weeks 1 through 16 (and two in week 17) 
for w in range (1,18):
    CName = '08_One_doubleheader_SUND_%s' % (w)
    if (w in range(1,17)):
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SUND','*')) == 1,
                                     name = CName)
    else:
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SUND','*')) == 2,
                                     name = CName)
nfl.update()
#%%There is exactly one Sunday Night Game per week in weeks 1 through 16 (no Sunday Night Game in week 17) 
for w in range (1,18):
    CName = '09_One_SUNN_%s' % (w)
    if(w in range(1,17)):
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SUNN','*')) == 1,
                                     name = CName)
    else:
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'SUNN','*')) == 0,
                                     name = CName)
nfl.update()
#%%Monday night games
eteam=list(teamdata.loc[teamdata["TIMEZONE"]==1,"TEAM"]) #Eastern Timezone
cteam=list(teamdata.loc[teamdata["TIMEZONE"]==2,"TEAM"]) #Central Timezone
mteam=list(teamdata.loc[teamdata["TIMEZONE"]==3,"TEAM"]) #Mountain Timezone
wteam=list(teamdata.loc[teamdata["TIMEZONE"]==4,"TEAM"]) #Western Timezone
non_wteam = mteam + eteam + cteam
for w in range(1,18):
    if(w == 1):
        CName = '10a_early_Mon_week_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'MON1','*')) == 1,
                                     name = CName)
        CName = '10b_WestCoast_Mon_Late_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',wteam,str(w),'MON2','*')) == 1,
                                     name = CName)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',non_wteam,str(w),'MON2','*')) == 0,
                                     name = CName)
    elif (w in range(2,17)):
        CName = '10c_One_Mon_night_week_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'MON1','*')) == 1,
                                     name = CName)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'MON2','*')) == 0,
                                     name = CName)
    elif(w==17):
        CName = '10c_One_Mon_night_week_%s' % (w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'MON1','*')) == 0,
                                     name = CName)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*','*',str(w),'MON2','*')) == 0,
                                     name = CName)
nfl.update()
#%%West Coast (LAC, SF, SEA, OAK, LAR) and Mountain Teams (DEN, ARZ) cannot play at home in the early Sunday time slot (SUNE)
mw_team = wteam + mteam
for t in mw_team:
    CName = '11_cannot_play_home_SUNE_%s' % (t)
    myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,'*','SUNE','*')) == 0,
                                     name = CName)
nfl.update()
#%%No team plays 4 consecutive home/away games in a season (treat a BYE as an away game)
for t in team:
    for w in range(1,15):
        w2 = [str(x) for x in range(w,w+4)]
        CName="12a_No_Consecutive_Home_Games_%s"%(t)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,str(w2),'*','*'))<=3,
                                             name = CName)
        CName="12b_No_Consecutive_Away_Games_%s"%(t)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',str(w2),'*','*'))+
                                         quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('BYE','*',str(w2),'*','*'))<=3,
                                            name = CName)
    del w2[:]
nfl.update()
#%%Each team must play at least 2 home/away games every 6 weeks
for t in team:
    for w in range(1,13):
        w2 = [str(x) for x in range(w,w+6)]
        CName="13a_Atleast_2Home_Games_6weeks_%s_%s"%(t,w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,w2,'*','*'))>=2,
                                             name = CName)
        CName="13b_Atleast_2Away_Games_6weeks_%s_%s"%(t,w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',w2,'*','*'))>=2,
                                             name = CName)
    del w2[:]
nfl.update()
#%%Each team must play at least 4 home/away games every 10 weeks
for t in team:
    for w in range(1,9):
        w2 = [str(x) for x in range(w,w+10)]
        CName="14a_Atleast_4Home_Games_10weeks_%s_%s"%(t,w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,w2,'*','*'))>=4,
                                             name = CName)
        CName="14b_Atleast_4Away_Games_10weeks_%s_%s"%(t,w)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',w2,'*','*'))>=4,
                                             name = CName)
    del w2[:]
nfl.update()
#%%All teams playing away on Thursday night are home the week before
for t in team:
    for w in range(2,18):
        CName="15_ThurNight_HomeWeekBefore_%s"%(t)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',str(w),'THUN','*'))-
                 quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,str(w-1),'*','*'))<=0,
                                          name = CName)
nfl.update()
#%%No team plays more than 2 road games against teams coming off a BYE 
Link_16 = {}
for t in team:
    for h in away[t]:
        if h!= 'BYE':
            for w in range(4,12):
                Lname = 'Link_16_%s_%s_%s' % (t,h,w)
                Link_16[t,h,str(w)] = nfl.addVar(obj = 0, vtype = GRB.BINARY, name = Lname)
nfl.update()
for t in team:
    for h in away[t]:
        if h!= 'BYE':
            for w in range(4,12):
                CName = '16_no_more_than_2_after_BYE_%s_%s_%s' % (t,h,w)
                myConstrs[CName] = nfl.addConstr(games[h,'BYE',str(w),'SUNB','BYE'] + 
                                                 quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,t,str(w+1),'*','*')) <= 1+Link_16[t,h,str(w)],
                                                 name = CName)               
nfl.update()
for t in team:
    for h in away[t]:
        if h!= 'BYE':
            CName = '16_CAP_%s' % t
            myConstrs[CName] = nfl.addConstr(quicksum(Link_16[t,h,str(w)] for w in range(4,12)) <= 2, name = CName)
nfl.update()
#%%Teams should not play 3 consecutive home/away games between weeks 4 through 16 (if a team does play 3 consecutive games home/away it can only happen once in the season for that team – either home or away) 
Pen_17a = {}
Pen_17h = {}
for t in team:
    for w in range(4,15):
        Lname = 'Link_17_%s_%s' % (t,w)
        Pen_17a[t,str(w)] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = Lname)
        Pen_17h[t,str(w)] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = Lname)
nfl.update()
for t in team:
    for w in range(4,15):
        w2 = [str(x) for x in range(w,w+3)]
        CName="17a_No_Consecutive_Home_Games_%s"%(t)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,str(w2),'*','*'))<=2+Pen_17h[t,str(w)],
                                             name = CName)
        CName="17b_No_Consecutive_Away_Games_%s"%(t)
        myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',str(w2),'*','*'))<=2+Pen_17a[t,str(w)],
                                             name = CName)
    del w2[:]
nfl.update()
for t in team:
    CName = '17_CAP_%s' % t
    myConstrs[CName] = nfl.addConstr(quicksum(Pen_17a[t,str(w)]+Pen_17h[t,str(w)] for w in range(4,15)) <= 1, name = CName)
nfl.update()
#%%No team should play consecutive road games involving travel across more than 1 time zone 
Penalty_18 = {}
for t in team:
    PName = 'Penalty_18_%s' % t
    Penalty_18[t] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = PName)
nfl.update()
x= mteam+wteam
y=eteam+cteam
for t in team:
    for h in away[t]:
        for w in range(1,18):
            w2 = [str(x) for x in range(w,w+2)]
            CName="18_No_Consecutive_Games_Across_Timezones_%s"%(t)
            if h in eteam:
                myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,x,str(w2),'*','*'))<=1+Penalty_18[t],name = CName)
            elif h in wteam:
                myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,y,str(w2),'*','*'))<=1+Penalty_18[t],name = CName)
            elif h in cteam:
                myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,wteam,str(w2),'*','*'))<=1+Penalty_18[t],name = CName)
            elif h in mteam:
                myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,eteam,str(w2),'*','*'))<=1+Penalty_18[t],name = CName)
    
nfl.update() 
del w2[:] 
#%%No team playing a Thursday night road game should travel more than 1 time zone from home
Penalty_19 = {}
for t in team:
    PName = 'Penalty_19_%s' % t
    Penalty_19[t] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = PName)
nfl.update()

for t in team:
    for h in away[t]:
        for w in range(1,18):
            CName="19_No_ThurNight_Travelling_Timezones_%s" % t
            if h in eteam:
                myConstrs[CName] = nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,x,str(w),'THUN','*'))<= 0+Penalty_19[t],name = CName)
            elif h in wteam:
                myConstrs[CName]= nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,y,str(w),'THUN','*'))<= 0+Penalty_19[t],name=CName)
            elif h in cteam:
                myConstrs[CName]= nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,wteam,str(w),'THUN','*'))<= 0+Penalty_19[t],name=CName)
            elif h in mteam:
                myConstrs[CName]= nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(h,eteam,str(w),'THUN','*'))<= 0+Penalty_19[t],name=CName)
    
nfl.update()  
#%%No team should open the season with two away games
Penalty_20 = {}
for t in team:
    PName = 'Penalty_20_%s' % t
    Penalty_20[t] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = PName)
nfl.update()

for t in team:
    w2 = ['1','2']
    CName="20_No_2_Away_Games_open_season_%s"%(t)
    myConstrs=nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',str(w2),'*','*'))<=1+Penalty_20[t],name=CName)
nfl.update()
del w2[:]
#%%No team should end the season with two away games
Penalty_21 = {}
for t in team:
    PName = 'Penalty_21_%s' % t
    Penalty_21[t] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = PName)
nfl.update()

for t in team:
    w2 = ['16','17']
    CName="21_No_2_Away_Games_end_season_%s"%(t)
    myConstrs=nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select(t,'*',str(w2),'*','*'))<=1+Penalty_21[t],name=CName)
nfl.update()
del w2[:]
#%%Florida teams should not play Early home games in the month of SEPT
fteam = ["JAC","MIA","TB"] #Florida teams
Penalty_22 = {}
for t in fteam:
    PName = 'Penalty_22_%s' % t
    Penalty_22[t] = nfl.addVar(obj = -4, vtype = GRB.BINARY, name = PName)
nfl.update()

for t in fteam:
     w2 = ['1','2','3','4']
     CName="22_No_Early_Home_Game_Sept_%s"%(t)
     myConstrs=nfl.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in gamelist.select('*',t,str(w2),'SUNE','*'))<=0+Penalty_22[t],name=CName)
nfl.update()
del w2[:]
#%%To create a database for nfl data
myConn = sqlite3.connect('nfl.db')
myCursor = myConn.cursor()
#%%To create a table that holds game variable information
gamedata.to_sql(name="tblgamevar",con=myConn,if_exists="replace")
#%%To create a table that holds the team data
teamdata.to_sql(name="tblteamdata",con=myConn,if_exists="replace")
#%% write the model to the directory and solve it
nfl.setParam('MIPFocus',1)
nfl.setParam('MIPGap',0.2)
nfl.write('test.lp')
nfl.optimize()
#%%print the solution to the screen
if nfl.Status == GRB.OPTIMAL:
    for a,h,w,s,n in gamevar:
        if games[a,h,w,s,n].x > 0:
            print( a,h,w,s,n, games[a,h,w,s,n].x* gamevar[a,h,w,s,n])
#%%To create solution table
if nfl.Status == GRB.OPTIMAL:
    myConn = sqlite3.connect('nfl.db')
    myCursor = myConn.cursor()
    nflSol = []
    for a,h,w,s,n in gamevar:
            if games[a,h,w,s,n].x > 0:
                nflSol.append((a,h,w,s,n, games[a,h,w,s,n].x* gamevar[a,h,w,s,n]))
    sqlString = """
                CREATE TABLE IF NOT EXISTS tblnflsol
                (Away      TEXT,
                 Home      TEXT,
                 Week      TEXT,
                 Slot      TEXT,
                 Network   TEXT,
                 Quality   DOUBLE);
                """
    myCursor.execute(sqlString)
    myConn.commit()
    
    # create the insert string
    sqlString = "INSERT INTO tblnflsol VALUES(?,?,?,?,?,?);"
    myCursor.executemany(sqlString, nflSol)    
    myConn.commit()
            
    myCursor.close()
    myConn.close()
#   
    print(nfl.ObjVal)