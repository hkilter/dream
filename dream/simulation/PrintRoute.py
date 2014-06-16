import Globals
import xlwt
from Globals import G

import OrderComponent
import Mould
import Order
import OrderDesign

JOB_SHOP_TECHNOLOGY_SEQ=['CAD','CAM','MILL','EDM','ASSM','MA','INJM','IM' ]
ORDER_COMPONENT_TYPE_SET=set(['OrderComponent','Design','Mould'])

def sortMachines():
    for tech in JOB_SHOP_TECHNOLOGY_SEQ:
        G.MachineList.sort(key=lambda x: x.id.startswith(tech))

def outputRoute():
    '''            
        prints the routes of the Jobs through the model as a table 
        the horizontal axis represents the different stations of the model 
        the vertical axis represents the time axis (events as points in time)
        each job will move through the stations for a specific time
        e.g.
    
    time\machines            M1        M2        M3        M4        M5
                
    t1                       J1
    t2                       J1                            J2
    t3                       J1                 J3         J2
    t4                       J1                 J3         J2        J4
    t5                                J2        J3                   J4
    t6                                J2        J3         J1        J4
    t7                                J2                   J1
    
        TODO: create multiple columns for each machine as one machine can receive more than one jobs at the same time (assembly)
        or can get an entity when an entity is removed from it (the cell of this machine for the specific time is occupied by the last
        job accessing it) 
    '''
    
    if G.trace=='Yes':
        if G.JobList:
            G.routeSheetIndex=G.sheetIndex+1
            # add one more sheet to the trace file
            G.routeTraceSheet=G.traceFile.add_sheet('sheet '+str(G.routeSheetIndex)+' route', cell_overwrite_ok=True)
            number_of_machines=len(G.MachineList)
            sortMachines()  # sort the machines according to the priority specified in JOB_SHOP_TECHNOLOGY_SEQ
            events_list=[]  # list to hold the events of the system
            # list all events
            for job in G.JobList:
                if job.schedule:
                    for record in job.schedule:
                        if not record[1] in events_list:
                            events_list.append(record[1])
                        if len(record)==3:
                            if not record[2] in events_list:
                                events_list.append(record[2])
            events_list.sort(cmp=None, key=None, reverse=False)     # sort the events
            number_of_events=len(events_list)                       # keep the total number of events 
            # create a table number_of_events X number_of_machines
            G.routeTraceSheet.write(0,0, 'Time/Machines')
            # write the events in the first column and the machineIDs in the first row
            for j, event in enumerate(events_list):
                G.routeTraceSheet.write(j+1,0,float(event))
            for j, machine in enumerate(G.MachineList):
                G.routeTraceSheet.write(0, j+1, str(machine.id))
            # sort the jobs according to their name
            G.JobList.sort(key=lambda x:x.id)
            # list of cells to be written
            cells=[]
            # orders that have aliases
            order_aliases=[]
            # indices of orders
            order_index=1
            # indices of jobs
            job_index=0
            # for every job in the JobList
            for job in G.JobList:
                job_index+=1
                # choose alias for the job
                try:
                    if not job.order in order_aliases:
                        job.order.alias='O'+str(order_index)
                        order_index+=1
                        order_aliases.append(job.order)
                    job.alias=job.order.alias+'J'+str(job_index)
                except:
                    job.alias='J'+str(job_index)
                if job.schedule:
                    for record in job.schedule:
                        # find the station of this step
                        station=record[0]               # XXX should also hold a list with all the machines G.MachineList?
                        # find the column corresponding to the machine
                        if station in G.MachineList:
                            machine_index=G.MachineList.index(station)
                            # find the entrance time of this step
                            entrance_time=record[1]         # the time entity entered station
                            # find the row corresponding to the event and start placing the name of the Job in the cells
                            entrance_time_index=events_list.index(entrance_time)
                            # find the exit time of this step
                            if len(record)==3:
                                exit_time=record[2]             # the time the entity exited the station
                                # find the row corresponding to the event and place the name of the Job in the cell, this is the last cell of this processing
                                exit_time_index=events_list.index(exit_time)
                            elif len(record)!=3:
                                exit_time_index=len(events_list)
                            # for the rows with indices entrance_time_index to exit_time_index print the id of the Job in the column of the machine_index
                            for step in range(entrance_time_index,exit_time_index+1, 1):
                                stepDone=False
                                # check if the cell is already written, if yes, then modify it adding the new jobs but not overwrite it
                                if not cells:
                                    cells.append({'row':step+1,
                                                  'col':machine_index+1,
                                                  'job':job.alias})
                                    G.routeTraceSheet.write(step+1, machine_index+1, job.alias)
                                    continue
                                
                                for cell in cells:
                                    if cell['row']==step+1 and cell['col']==machine_index+1:
                                        cell['job']=cell['job']+','+job.alias
                                        G.routeTraceSheet.write(cell['row'], cell['col'], cell['job'])
                                        stepDone=True
                                        break
                                if not stepDone:
                                    cells.append({'row':step+1,
                                                  'col':machine_index+1,
                                                  'job':job.alias})
                                    G.routeTraceSheet.write(step+1, machine_index+1, job.alias)
            # print aliases
            try:
                sample_job=next(x for x in G.JobList)
                if sample_job.__class__.__name__ in ORDER_COMPONENT_TYPE_SET:
                    G.JobList.sort(key=lambda x:x.order.id)
            except:
                pass
            for j,job in enumerate(G.JobList):
                if job.schedule:
                    G.routeTraceSheet.write(number_of_events+2+j, 0, job.id)
                    G.routeTraceSheet.write(number_of_events+2+j, 1, job.alias)
            
