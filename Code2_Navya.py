# -*- coding: utf-8 -*-
"""
Created on Thu Apr 19 10:49:14 2018

@author: Navya
#  OR 604-Section 01 Practical Optimization - Spring of 2018
#  HW 9/11 - NFL Case Study (Serial Processing of NFL Model)
# Jem Anderson & Navya
# mailto:     jander42@masonlive.gmu.edu 
# mailto:     nmote@masonlive.gmu.edu
"""
import csv
from gurobipy import *
#%% Write Python script that reads in NFL model 

NFL = Model()
NFL = read("OR604 Model File v2.lp")
#%% 
#  Read model variables and select game variables
myVars = NFL.getVars()
games = {}
for v in myVars:
    if v.varName[:2] == 'GO':
        games[v.varName] = v
#%%
#  Read constraints and, for hard constraints whose right hand size is <=0, set game variables to zero
VarBounds_Zero = {}
VarBounds_NotZero = {}
myConstrs = NFL.getConstrs()
for c in myConstrs:
    if c.sense == '<' and c.RHS == 0:
        row=NFL.getRow(c)
        myFlag=True
        for r in range(row.size()):
            if row.getVar(r).varName[:2] !='GO':
                myFlag=False
            if myFlag:
                row.getVar(r).lb = 0
                row.getVar(r).ub = 0
                NFL.update()
                VarBounds_Zero[row.getVar(r).varName] = (row.getVar(r).lb, row.getVar(r).ub) # Added by NM
    else:
        row=NFL.getRow(c)
        for r in range(row.size()):
            if row.getVar(r).varName[:2] =='GO':
                if row.getVar(r).lb != row.getVar(r).ub:
                    VarBounds_NotZero[row.getVar(r).varName] = (row.getVar(r).lb, row.getVar(r).ub)
with open('VarBounds_zero.csv', 'wb') as f:
    w = csv.writer(f)
    for row in VarBounds_Zero.iteritems():
        w.writerow(row)
with open('VarBounds_not_zero.csv', 'wb') as f:
    w = csv.writer(f)
    for row in VarBounds_NotZero.iteritems():
        w.writerow(row)
NFL.update()
#%%Probing
#Begin of additions by NM
VarBounds_Free={}
VarBounds_FreePrime={}
VarBounds_SetZero={}
count=0
count2 =0
count3 = 0
myFlag = True
while myFlag:
    for v in myVars:
        if v.varName in VarBounds_NotZero:
            if VarBounds_NotZero[v.varName][0]!= VarBounds_NotZero[v.varName][1]:
                vsplit = v.varName.split('_')
                v.lb = 1
                v.ub = 1
                NFL.update()
                NFL.setParam('TimeLimit',15)
                NFL.optimize()
                if NFL.status == GRB.INFEASIBLE:
                    v.lb = 0
                    v.ub = 0
                    NFL.update()
                    VarBounds_NotZero[v.varName] = (v.lb, v.ub)
                    VarBounds_SetZero[v.varName] = (v.lb, v.ub)
                    myFlag = True
                    count3 = count3 + 1
                    print "Infeasible count is:",count3
                    print "Feasible count is:",count
                    print "LP count is:",count2
                    y = len(VarBounds_FreePrime.keys())
                    print "No. of Prime Var:",y
                    x = len(VarBounds_Free.keys())
                    print "No. of Free Var:",x
                    VarBounds_FreePrime.pop(v.varName, None)
                else:
                    v.lb = 0
                    v.ub = 1
                    NFL.update()
                    VarBounds_NotZero[v.varName] = (v.lb, v.ub)
                    VarBounds_Free[v.varName] = (v.lb, v.ub)
                    x = len(VarBounds_Free.keys())
                    print "No. of Free Var:",x
                    myFlag = True
                    count = count + 1
                    print "Infeasible count is:",count3
                    print "Feasible count is:",count
                    print "LP count is:",count2
                    x = len(VarBounds_Free.keys())
                    print "No. of Free Var:",x
                    y = len(VarBounds_FreePrime.keys())
                    print "No. of Prime Var:",y
                if VarBounds_NotZero[v.varName][0]!= VarBounds_NotZero[v.varName][1]:
                    myFlag = True
                    if VarBounds_NotZero[v.varName][0]!= VarBounds_NotZero[v.varName][1] and vsplit[4] == 'PRIME':
                        VarBounds_FreePrime[v.varName] = (v.lb, v.ub)
                        y = len(VarBounds_FreePrime.keys())
                        print "No. of Prime Var:",y
                        with open('VarBounds_FreePrime.csv', 'wb') as f:
                            w = csv.writer(f)
                            for row in VarBounds_FreePrime.iteritems():
                                w.writerow(row)
                else:
                    count2 = count2 + 1
                    print "LP count is:",count2
                    NFL.write("myFile.lp")
                    myFlag = False 
NFL.update()