# ===========================================================================
# Copyright 2013 University of Limerick
#
# This file is part of DREAM.
#
# DREAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DREAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
# ===========================================================================

'''
Created on 23 March 2015

@author: Panos
'''
import ImportDatabase 
from datetime import datetime
#connect to the database providing the following data and generate six different cursor variables
cnxn=ImportDatabase.ConnectionData(seekName='ServerData', implicitExt='txt', number_of_cursors=6)
cursor=cnxn.getCursors()
#SQL query to extract data from orders table
a=cursor[0].execute("""
        select Order_id, ProjectName, Customer, Order_date, Due_date, ProjectManager, Status
        from orders
                """)
#create a dictionary called data and put inside two lists (orders and stations) and a dictionary called WIP
data={}
data['orders']=[]
data['WIP']={}
data['stations']=[]
order={}
#Another SQL query that extracts data from the machines table
b=cursor[1].execute("""
        select MachineName, description
        from machines
                """)
# for every machine of the machines table
for j in range(b.rowcount):
    #get the next line
    ind3=b.fetchone() 
    #and insert in one of the above initiated lists
    data['stations'].append(ind3.MachineName)

# for every order of the orders table
for j in range(a.rowcount):
    #get the next line
    ind0=a.fetchone() 
    #define a variable called status and holds the status of the order (extracted from orders table)
    status = ind0.Status
    #check if status is 'accepted' or 'in progress' and move in
    if status == 'accepted' or status == 'in progress':
        #insert the following extracted data from the database in order disctionary
        order['orderName']=ind0.ProjectName
        order['orderID']=ind0.Order_id
        order['manager']=ind0.ProjectManager
        order['orderDate']=ind0.Order_date
        order['dueDate']=ind0.Due_date
        order['componentsList']=[]
        #SQL query to extract data from sequence table where order data is given
        c=cursor[2].execute("""
                    select Order_id, WP_id, PartCode, PartName, Operation_Name, ProcessingTime, PersonnelCode, Quantity, step
                    from sequence where Order_id=?
                    """, ind0.Order_id)
        
        appended=[] # list that holds the already added components
        # for all the lines of c (every component)
        for i in range(c.rowcount):
            # create a comopnent dict
            component={}
            # and get the next row
            ind1=c.fetchone()
            name=ind1.PartName
            component['componentName']=name
            code=ind1.PartCode
            WP=ind1.WP_id
            component['componentID']=code
            component['route']=[]
            #SQL query that extracts data from sequence table where PartCode is given
            d=cursor[3].execute("""
                    select  PartCode, PartName, WP_id, Operation_Name, ProcessingTime, PersonnelCode, Quantity, step
                    from sequence
                    where PartCode=?
                    """, code)
            #SQL query that joins the sequence and prerequisites tables where WP_id is common and PartCode is given 
            f=cursor[4].execute("""
                    select  sequence.WP_id, sequence.PartCode, prerequisites.PartsNeeded
                    from sequence, prerequisites 
                    where sequence.WP_id=prerequisites.WP_id
                    AND sequence.PartCode=?
                    """, code)        
            #loop every line in the sequence table
            for line in range(d.rowcount):
                #create a new dictionary to hold the sequence of this order
                step={}
                ind2=d.fetchone()
                step['technology']=ind2.Operation_Name
                step['sequence']=ind2.step
                step['operator']=ind2.PersonnelCode
                step['task_id']=ind2.WP_id
                step['quantity']=ind2.Quantity
                ind3=f.fetchone()
                partsNeeded = ind3.PartsNeeded.split(';')       
                step['partsneeded']=partsNeeded       
                step['processingTime']={}
                step['processingTime']['distribution']='Fixed'
                step['processingTime']['mean']=ind2.ProcessingTime  
                component['route'].append(step)
            #The following checks if the component ids have been inserted to appended   
            if not component['componentID'] in appended:
                order['componentsList'].append(component)
                appended.append(component['componentID'])
                #SQL query to extract WIP data from the prod_status table when sequence and prod_status are joined together and PartCode is given
                e= cursor[5].execute("""
                    select prod_status.WP_id, sequence.WP_id, sequence.ProcessingTime, sequence.step, MachineName, TIMEIN, TIMEOUT, prod_status.PersonnelCode
                    from prod_status 
                    join sequence on sequence.WP_id = prod_status.WP_id
                    where sequence.PartCode=?
                    """, code)
                #loop in the lines of the prod_status table 
                for x in range(e.rowcount):
                    ind3=e.fetchone()
                    
                    for t in appended:
                        if ind3.TIMEOUT:
                            remTime= 0
                        else:
                            #calculate the time difference between the TIMEIN and the moment the user wants to run the simulation (e.g. datetime.now())
                            timeDelta= datetime.now() - ind3.TIMEIN
                            timeDiff= timeDelta.total_seconds() / 3600
                            #calculate the remaining time the part needs to be processed 
                            remTime= round((ind3.ProcessingTime - timeDiff),2) 
                            
                        data['WIP'][code]={}
                        data['WIP'][code]['station']=ind3.MachineName
                        data['WIP'][code]['operator']=ind3.PersonnelCode
                        data['WIP'][code]['task_id']=ind3.WP_id
                        data['WIP'][code]['sequence']=ind3.step
                        data['WIP'][code]['remainingProcessingTime']=remTime
    #in case the status is 'finished' continue to the next order                                   
    elif status == 'finished':
        continue    
    data['orders'].append(order.copy())           

print data