import geopy
import csv
import sqlite3
from gurobipy import *
import pandas as pd
#%% import distributionc center data
DistributionCenter={}
with open("distributionCenter.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        DistributionCenter[row[0]] = (float(row[1]), float(row[2]))
#%%%% importing the supply demand of distribution center from the csv file
supply={}
with open("supply.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        supply[row[0]] = int(row[1])
#%%%% importing the supply capacity of supplier from the csv file
suppliercap={}
with open("supplier.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        suppliercap[row[0]] = int(4.0*int(row[1])/7)        
#%% import cost function
supplierstate={}
with open("supplierstate.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        supplierstate[row[0]] = str(row[1])    
#%%Supplier Running cost
supplierop={}
with open("supplier_op.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        supplierop[row[0]] = int(row[1])         
#%% Supplier location data    
Supplier={}
with open("supplydata.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        Supplier[row[0]] = (float(row[1]), float(row[2]))            
#%%Caluclating the distance from supplier to distribution center    
supplierdistance={}
from geopy.distance import vincenty
for st in Supplier:
    for dc in DistributionCenter:
        supplierdistance[(st,dc)]=vincenty(Supplier[st],DistributionCenter[dc]).miles     
#%%supplier cost
Suppliercost={}
with open("cost.csv", "r") as myCSV:
    myReader = csv.reader(myCSV)
    for row in myReader:
        Suppliercost[row[0]] = (float(row[1]))        
#%%
Midwest=["MI","MO","MN","IA","IL","IN","KS","NE","ND","OH","SD","WI"]
Southeast=["KY","GA","FL","AL","DC","MS","NC","SC","TN","WV","VA"]
Northeast=["MD","NC","CT","DE","MA","ME","NH","NJ","NY","PA","RI","VT"]
Southwest=["LA","TX","OK"]
West=["CO","AZ","WA","CA","AR","ID","AK","HI","MT","NV","NM","OR","UT","WY"]
#%%Assigning distribution cost            
supdcost={}

for st in Supplier:
        if supplierstate[st] in Midwest:
            supdcost[st]= 1.64;
        elif supplierstate[st] in Southeast:
            supdcost[st]= 1.68;
        elif supplierstate[st] in Southwest:
            supdcost[st]= 1.67;
        elif supplierstate[st] in Northeast:
            supdcost[st]= 1.79;
        elif supplierstate[st] in West:
            supdcost[st]= 1.77;
        else:
            supdcost[st]=100000000            
        
#%% Create the model
charpizza = Model()
charpizza.modelSense = GRB.MINIMIZE
charpizza.update()
#%% create the variables

# create a dictionary that will contain the gurobi variable objects
mypizza = {}
for st in suppliercap:
    for dc in supply:
        mypizza[st,dc] = charpizza.addVar(obj = ( ( supdcost[st]*supplierdistance[st,dc]*supply[dc] )/880 + ( supply[dc]*Suppliercost[st] ) ), 
                                   vtype = GRB.BINARY, 
                                   name = 'x_%s_%s' % ([st,dc][1], [st,dc][0]))
charpizza.update()
#%%
rc_mill = {}
for st in suppliercap:
    VarName = 'running_cost_%s' %st
    rc_mill[st] = charpizza.addVar(obj = supplierop[st], vtype = GRB.BINARY, name = VarName)
charpizza.update()    
#%% create the supply constraints
myConstrs = {}
for st in Supplier:
    constrName = 'supply'
    myConstrs[constrName] = charpizza.addConstr(quicksum(mypizza[st,dc]*supply[dc] for dc in DistributionCenter) 
                                               <= suppliercap[st]*rc_mill[st], name = constrName)
charpizza.update()
#%%create the demand constrain
for dc in DistributionCenter:
    constrName = 'demand' 
    myConstrs[constrName] = charpizza.addConstr(lhs=(quicksum(mypizza[st,dc] for st in Supplier)),sense = GRB.EQUAL,
             rhs = 1, name = constrName)
charpizza.update()
    
#%%% create non negativity constrains
for st in Supplier:
    for dc in DistributionCenter:
        constrName = 'nonnegatavity'
        myConstrs[constrName] = charpizza.addConstr(mypizza[st,dc] 
                                               >=0 , 
                                               name = constrName)
charpizza.update()
    
    
#%% write the model to the directory and solve it
charpizza.setParam('MIPFocus',1)
charpizza.setParam('MIPGap',0.2)
charpizza.write('test.lp')
charpizza.optimize()

#%% print the solution to the screen
if charpizza.Status == GRB.OPTIMAL:
 for st in Supplier:    
    for dc in DistributionCenter:
            if mypizza[st,dc].x > 0:
                print( st,dc, mypizza[st,dc].x* supply[dc])
                
        
#%% save results in a database
if charpizza.Status == GRB.OPTIMAL:
    myConn = sqlite3.connect('charPizza.db')
    myCursor = myConn.cursor()
    pizzaSol = []
    for st in Supplier:
        for dc in DistributionCenter:
            if mypizza[st,dc].x > 0:
                pizzaSol.append((st,dc, mypizza[st,dc].x* supply[dc]))
                
#            df=pd.read_sql_query("SELECT DISTINCT(Supplier) from tblpizza",myConn)
#            tot_rows = df.count()
#            value = int (tot_rows * 3000000)
        

    # create the table    
    sqlString = """
                CREATE TABLE IF NOT EXISTS tblPizza
                (Supplier      TEXT,
                 Distribution Center           TEXT,
                 QTY            DOUBLE);
                """
    myCursor.execute(sqlString)
    myConn.commit()
    
    # create the insert string
    sqlString = "INSERT INTO tblPizza VALUES(?,?,?);"
    myCursor.executemany(sqlString, pizzaSol)    
    myConn.commit()
            
    myCursor.close()
    myConn.close()
#   
    print(charpizza.ObjVal)