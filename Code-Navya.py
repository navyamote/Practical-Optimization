# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 23:35:33 2018

@author: Navya
"""
import geopy
import csv
import pandas as pd
import pandas.io.sql as pd_sql
import sqlite3
from gurobipy import *
#%%To get the Game variables
gamevar={}
with open("GameVariables_2018.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        gamevar[row[0], row[1], row[2], row[3], row[4]] = ((row[5]))
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
#%%To get the conferences
conf={}        
with open("TEAM_DATA_2018.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)      
    for row in myReader:
        if row[1] not in conf:
            conf[row[1]] = []
        conf[row[1]].append(row[0])
#%%To get the divisions    
div={}  
with open("TEAM_DATA_2018.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)        
    for row in myReader:
        if row[1] not in div:
            div[row[1]] = {}
        if row[2] not in div[row[1]]:
            div[row[1]][row[2]]= []
        div[row[1]][row[2]].append(row[0])      
#%%To get the Game list
gamelist=[]
for a,h,w,s,n in gamevar:
    gamelist.append((a,h,w,s,n))
gamelist = tuplelist(gamelist)        