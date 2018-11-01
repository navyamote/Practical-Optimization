import csv
from gurobipy import *
import sqlite3
#%% Load yeast supply and amount per beer type

Supply = {}
with open("Supply.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        Supply[row[0]] = (int(row[1]))
#%% load hop supply and amount per beer type

profit = {}
with open("Profit.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        profit[row[0]] = (int(row[1]))
        
#%% load grain supply and amount per beer type        
Demand = {}
with open("Demand.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        Demand[row[0].replace(" ",""), row[1]] = (float(row[2]))
        
#%% Create the model
charBrew = Model()
charBrew.modelSense = GRB.MAXIMIZE
charBrew.update()

#%% create the variables

# create a dictionary that will contain the gurobi variable objects
myBeer = {}
for beer in profit: 
    myBeer[beer] = charBrew.addVar(obj = profit[beer], 
                                   vtype = GRB.CONTINUOUS, 
                                   name = beer)
charBrew.update()

#%% create the Grain constraints

# create a dictionary that holds all constraints
Grain=['Barley','Hops']
myConstrs = {}
for grain in Grain:
    constrName = grain
    myConstrs[constrName] = charBrew.addConstr(quicksum(Demand[b,grain]*myBeer[b] for b in profit) 
                                               <= Supply[grain], name = constrName)
charBrew.update()
    

for beer in profit:
    constrName = '%s_min_demand' % beer
    myConstrs[constrName] = charBrew.addConstr(myBeer[beer] 
                                               >=0 , 
                                               name = constrName)
charBrew.update()
    
    
#%% write the model to the directory and solve it
charBrew.write('test.lp')
charBrew.optimize()

#%% print the solution to the screen
if charBrew.Status == GRB.OPTIMAL:
    for beer in profit:
        if myBeer[beer].x > 0:
            print( beer, myBeer[beer].x)
        
#%% save results in a database
if charBrew.Status == GRB.OPTIMAL:
    myConn = sqlite3.connect('charBrew.db')
    myCursor = myConn.cursor()
    beerSol = []
    for beer in myBeer:
        if myBeer[beer].x > 0:
            beerSol.append((myBeer[beer].varName, myBeer[beer].x))

    # create the table    
    sqlString = """
                CREATE TABLE IF NOT EXISTS tblBeer
                (BEER_TYPE      TEXT,
                 QTY            DOUBLE);
                """
    myCursor.execute(sqlString)
    myConn.commit()
    
    # create the insert string
    sqlString = "INSERT INTO tblBeer VALUES(?,?);"
    myCursor.executemany(sqlString, beerSol)    
    myConn.commit()
            
    myCursor.close()
    myConn.close()
   
    
