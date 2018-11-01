import csv
from gurobipy import *
import sqlite3


#%% load beer profit and minimum demand
steelcost = {}
with open("steelcost.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        steelcost[row[0].replace(" ",""), row[1]] = (int(row[2]))
   


#%% Load yeast supply and amount per beer type

steeldemand = {}
with open("steeldemand.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        steeldemand[row[0]] = (int(row[1]))

steeltime = {}
with open("steeltime.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        steeltime[row[0].replace(" ",""), row[1]] = (float(row[2]))

#%% Create the model
charsteel = Model()
charsteel.modelSense = GRB.MINIMIZE
charsteel.update()
mysteel = {}
steeltype=['steel1','steel2',]
milltype=['mill1','mill2','mill3']
for steel in steeltype:
    for mill in milltype:
        steeltemp=(steel,mill)
        mysteel[steeltemp] = charsteel.addVar(obj = steelcost[steeltemp], 
                                   vtype = GRB.CONTINUOUS, 
                                   name = steel)
charsteel.update()

#%%time constrains

myConstrs = {}
for mill in milltype:
    constrName = '%s_time' %mill
    myConstrs[constrName] = charsteel.addConstr(quicksum(steeltime[(s,mill)]*mysteel[(s,mill)] for s in steeltype) 
                                               <=200 , name = constrName)
charsteel.update()
for steel in steeltype:
    constrName='%s_minimum_demand' %steel
    myConstrs[constrName] = charsteel.addConstr(quicksum(mysteel[(steel,mill)] for mill in milltype) >= steeldemand[steel],name=constrName)
for steel in steeltype:   
     for mill in milltype:
         constrName ='{0} {1}'.format(steel,mill)
         steeltemp=(steel, mill)
         myConstrs[constrName] = charsteel.addConstr(mysteel[steeltemp] 
                                               >=0 , 
                                               name = constrName)
charsteel.update()
    
    
#%% write the model to the directory and solve it
charsteel.write('test.lp')
charsteel.optimize()

#%% print the solution to the screen
if charsteel.Status == GRB.OPTIMAL:
    for steel in mysteel:
        if mysteel[steel].x > 0:
            print( steel, mysteel[steel].x)
        
#%% save results in a database
if charsteel.Status == GRB.OPTIMAL:
    myConn = sqlite3.connect('charsteel.db')
    myCursor = myConn.cursor()
    steelSol = []
    for steel in mysteel:
        if mysteel[steel].x > 0:
            steelSol.append((mysteel[steel].varName, mysteel[steel].x))

    # create the table    
    sqlString = """
                CREATE TABLE IF NOT EXISTS tblsteel
                (steel_TYPE      TEXT,
                 QTY            DOUBLE);
                """
    myCursor.execute(sqlString)
    myConn.commit()
    
    # create the insert string
    sqlString = "INSERT INTO tblsteel VALUES(?,?);"
    myCursor.executemany(sqlString, steelSol)    
    myConn.commit()
            
    myCursor.close()
    myConn.close()
   
print(charsteel.ObjVal)
