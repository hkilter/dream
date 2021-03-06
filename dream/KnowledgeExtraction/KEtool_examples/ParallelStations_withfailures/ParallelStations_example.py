'''
Created on 15 Jun 2014

@author: Panos
'''
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

from Transformations import BasicTransformations
from DistributionFitting import DistFittest
from DistributionFitting import Distributions
from ExcelOutput import Output
import ImportDatabase
import json

#================================= Extract data from the database ==========================================#

cnxn=ImportDatabase.ConnectionData(seekName='ServerData', implicitExt='txt', number_of_cursors=3)
cursors=cnxn.getCursors()

a = cursors[0].execute("""
        select prod_code, stat_code,emp_no, TIMEIN, TIMEOUT
        from production_status
                """)
MILL1=[]
MILL2=[]
for j in range(a.rowcount):
    #get the next line
    ind1=a.fetchone() 
    if ind1.stat_code == 'MILL1':
        procTime=[]
        procTime.insert(0,ind1.TIMEIN)
        procTime.insert(1,ind1.TIMEOUT)
        MILL1.append(procTime)
    elif ind1.stat_code == 'MILL2':
        procTime=[]
        procTime.insert(0,ind1.TIMEIN)
        procTime.insert(1,ind1.TIMEOUT)
        MILL2.append(procTime)
    else:
        continue
    
transform = BasicTransformations()
procTime_MILL1=[]
for elem in MILL1:
    t1=[]
    t2=[]
    t1.append(((elem[0].hour)*60)*60 + (elem[0].minute)*60 + elem[0].second)
    t2.append(((elem[1].hour)*60)*60 + (elem[1].minute)*60 + elem[1].second)
    dt=transform.subtraction(t2, t1)
    procTime_MILL1.append(dt[0])

procTime_MILL2=[]
for elem in MILL2:
    t1=[]
    t2=[]
    t1.append(((elem[0].hour)*60)*60 + (elem[0].minute)*60 + elem[0].second)
    t2.append(((elem[1].hour)*60)*60 + (elem[1].minute)*60 + elem[1].second)
    dt=transform.subtraction(t2, t1)
    procTime_MILL2.append(dt[0])


b = cursors[1].execute("""
        select stat_code, MTTF_hour
        from failures
                """)

c = cursors[2].execute("""
        select stat_code, MTTR_hour
        from repairs
                """)         
MTTF_MILL1=[]
MTTF_MILL2=[]
for j in range(b.rowcount):
    #get the next line
    ind2=b.fetchone() 
    if ind2.stat_code == 'MILL1':
        MTTF_MILL1.append(ind2.MTTF_hour)
    elif ind2.stat_code == 'MILL2':
        MTTF_MILL2.append(ind2.MTTF_hour)
    else:
        continue

MTTR_MILL1=[]
MTTR_MILL2=[]
for j in range(c.rowcount):
    #get the next line
    ind3=c.fetchone() 
    if ind3.stat_code == 'MILL1':
        MTTR_MILL1.append(ind3.MTTR_hour)
    elif ind3.stat_code == 'MILL2':
        MTTR_MILL2.append(ind3.MTTR_hour)
    else:
        continue

#======================= Fit data to statistical distributions ================================#
dist_proctime = DistFittest()
distProcTime_MILL1 = dist_proctime.ks_test(procTime_MILL1)
distProcTime_MILL2 = dist_proctime.ks_test(procTime_MILL2)

dist_MTTF = Distributions()
dist_MTTR = Distributions()
distMTTF_MILL1 = dist_MTTF.Weibull_distrfit(MTTF_MILL1)
distMTTF_MILL2 = dist_MTTF.Weibull_distrfit(MTTF_MILL2)

distMTTR_MILL1 = dist_MTTR.Poisson_distrfit(MTTR_MILL1)
distMTTR_MILL2 = dist_MTTR.Poisson_distrfit(MTTR_MILL2) 

#======================= Output preparation: output the updated values in the JSON file of this example ================================#
jsonFile = open('JSON_example.json','r')      #It opens the JSON file 
data = json.load(jsonFile)                                                              #It loads the file
jsonFile.close()
nodes = data.get('nodes',[])                                                         #It creates a variable that holds the 'nodes' dictionary

for element in nodes:
    processingTime = nodes[element].get('processingTime',{})        #It creates a variable that gets the element attribute 'processingTime'
    MTTF_Nodes = nodes[element].get('MTTF',{})                            #It creates a variable that gets the element attribute 'MTTF'
    MTTR_Nodes = nodes[element].get('MTTR',{})                            #It creates a variable that gets the element attribute 'MTTR'
        
    if element == 'M1':
        nodes['M1']['processingTime'] = distProcTime_MILL1         #It checks using if syntax if the element is 'M1'
        nodes['M1']['failures']['MTTF'] = distMTTF_MILL1
        nodes['M1']['failures']['MTTR'] = distMTTR_MILL1
    elif element == 'M2':
        nodes['M2']['processingTime'] = distProcTime_MILL2         #It checks using if syntax if the element is 'M2'
        nodes['M2']['failures']['MTTF'] = distMTTF_MILL2
        nodes['M2']['failures']['MTTR'] = distMTTR_MILL2
    
    jsonFile = open('JSON_ParallelStations_Output.json',"w")     #It opens the JSON file
    jsonFile.write(json.dumps(data, indent=True))                                           #It writes the updated data to the JSON file 
    jsonFile.close()                                                                        #It closes the file

#=================== Calling the ExcelOutput object, outputs the outcomes of the statistical analysis in xls files ==========================#
export=Output()

export.PrintStatisticalMeasures(procTime_MILL1,'procTimeMILL1_StatResults.xls')   
export.PrintStatisticalMeasures(procTime_MILL2,'procTimeMILL2_StatResults.xls')
export.PrintStatisticalMeasures(MTTF_MILL1,'MTTFMILL1_StatResults.xls')   
export.PrintStatisticalMeasures(MTTF_MILL2,'MTTFMILL2_StatResults.xls')
export.PrintStatisticalMeasures(MTTR_MILL1,'MTTRMILL1_StatResults.xls')   
export.PrintStatisticalMeasures(MTTR_MILL2,'MTTRMILL2_StatResults.xls')

export.PrintDistributionFit(procTime_MILL1,'procTimeMILL1_DistFitResults.xls')
export.PrintDistributionFit(procTime_MILL2,'procTimeMILL2_DistFitResults.xls')
export.PrintDistributionFit(MTTF_MILL1,'MTTFMILL1_DistFitResults.xls')
export.PrintDistributionFit(MTTF_MILL2,'MTTFMILL2_DistFitResults.xls')
export.PrintDistributionFit(MTTR_MILL1,'MTTRMILL1_DistFitResults.xls')
export.PrintDistributionFit(MTTR_MILL2,'MTTRMILL2_DistFitResults.xls')