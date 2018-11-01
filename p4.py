import geopy
import csv
import sqlite3
from gurobipy import *
import pandas as pd

#%%%%%%% import stores data 
stores={}
with open("storealive.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        stores[row[0]] = (float(row[6]), float(row[7]))



#%%%%%%% import distributionc center data
DistributionCenter={}
with open("distributionCenter.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        DistributionCenter[row[0]] = (float(row[1]), float(row[2]))
#%%%%%%%% Caluclating the distance from distribution center to store
distance={}
from geopy.distance import vincenty
for st in stores:
    for dc in DistributionCenter:
        distance[(dc,st)]=vincenty(DistributionCenter[dc],stores[st]).miles
        
#%%%% importing the supply from the csv file
supply={}
with open("supply.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        supply[row[0]] = int(row[1])
#%% import demand from the csv file
demand ={}
with open("weekdemand.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        demand[row[0]] = float(row[1])

#%% import cost function
distributionstate={}
with open("distributionCenterstate.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        distributionstate[row[0]] = str(row[1])
#%%
storestate={}
with open("storestate.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        storestate[row[0]] = str(row[1])
#%%
Midwest=["MI","MO","MN","IA","IL","IN","KS","NE","ND","OH","SD","WI"]
Southeast=["KY","GA","FL","AL","DC","MS","NC","SC","TN","WV"]
Northeast=["MD","NC","CT","DE","MA","ME","NH","NJ","NY","PA","RI","VT"]
Southwest=["LA","TX","OK"]
West=["CO","AZ","WA","CA","AR","ID","AK","HI","MT","NV","NM","OR","UT","WY"]
#%%%
cost={}

for ds in distributionstate:
    for ss in storestate:  
        if distributionstate[ds] in Midwest and storestate[ss] in Midwest:
            cost[(ds,ss)]= 1.64;
        elif distributionstate[ds] in Southeast and storestate[ss] in Southeast:
            cost[(ds,ss)]= 1.68;
        elif distributionstate[ds] in Southwest and storestate[ss] in Southwest:
            cost[(ds,ss)]= 1.67;
        elif distributionstate[ds] in Northeast and storestate[ss] in Northeast:
            cost[(ds,ss)]= 1.79;
        elif distributionstate[ds] in West and storestate[ss] in West:
            cost[(ds,ss)]= 1.77;
        else:
            cost[(ds,ss)]=10000000
            
        
#%% Create the model
charpizza = Model()
charpizza.modelSense = GRB.MINIMIZE
charpizza.update()

#%% create the variables

# create a dictionary that will contain the gurobi variable objects
mypizza = {}
for dc in supply:
    for st in stores:
        mypizza[dc,st] = charpizza.addVar(obj = ( cost[dc,st]*distance[dc,st] )/9900, 
                                   vtype = GRB.CONTINUOUS, 
                                   name = 'x_%s_%s' % ([dc,st][1], [dc,st][0]))
charpizza.update()

#%% create the supply constraints
myConstrs = {}
for dc in DistributionCenter:
    constrName = 'supply'
    myConstrs[constrName] = charpizza.addConstr(quicksum(mypizza[dc,st] for st in stores) 
                                               <= supply[dc], name = constrName)
charpizza.update()
#%%create the demand constrain
for st in stores:
    constrName = 'demand' 
    myConstrs[constrName] = charpizza.addConstr(quicksum(mypizza[dc,st] for dc in DistributionCenter) 
                                               >= demand[st], name = constrName)
charpizza.update()
    
#%%% create non negativity constrains
for dc in DistributionCenter :
    for st in stores:
        constrName = 'nonnegatavity'
        myConstrs[constrName] = charpizza.addConstr(mypizza[dc,st] 
                                               >=0 , 
                                               name = constrName)
charpizza.update()
    
    
#%% write the model to the directory and solve it
charpizza.write('test.lp')
charpizza.optimize()

#%% print the solution to the screen
if charpizza.Status == GRB.OPTIMAL:
    for dc in DistributionCenter:
        for st in stores:
            if mypizza[dc,st].x > 0:
                print( dc,st, mypizza[dc,st].x)
                
        
#%% save results in a database
if charpizza.Status == GRB.OPTIMAL:
    myConn = sqlite3.connect('charPizza.db')
    myCursor = myConn.cursor()
    pizzaSol = []
    for pizza in mypizza:
        if mypizza[pizza].x > 0:
            pizzaSol.append((mypizza[pizza].varName, mypizza[pizza].x))

    # create the table    
    sqlString = """
                CREATE TABLE IF NOT EXISTS tblPizza
                (PIZZA      TEXT,
                 QTY            DOUBLE);
                """
    myCursor.execute(sqlString)
    myConn.commit()
    
    # create the insert string
    sqlString = "INSERT INTO tblPizza VALUES(?,?);"
    myCursor.executemany(sqlString, pizzaSol)    
    myConn.commit()
            
    myCursor.close()
    myConn.close()
#   
    print(charpizza.ObjVal)