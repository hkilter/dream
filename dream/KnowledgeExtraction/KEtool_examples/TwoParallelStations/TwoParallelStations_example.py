'''
Created on 20 Jun 2014

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

from DistributionFitting import DistFittest
from DistributionFitting import Distributions
from ImportExceldata import Import_Excel
from ExcelOutput import Output
from ReplaceMissingValues import HandleMissingValues
from JSONOutput import JSONOutput
import xlrd
import json
import dream.simulation.LineGenerationJSON as ManPyMain #import ManPy main JSON script

#Read from the given directory the Excel document with the input data
workbook = xlrd.open_workbook('inputData.xls')
worksheets = workbook.sheet_names()
worksheet_ProcessingTimes = worksheets[0]     #Define the worksheet with the Processing times data

inputData = Import_Excel()                              #Call the Python object Import_Excel
ProcessingTimes = inputData.Input_data(worksheet_ProcessingTimes, workbook)   #Create the Processing Times dictionary with key Machines 1,2 and values the processing time data

##Get from the above dictionaries the M1 key and define the following lists with data 
M1_ProcTime = ProcessingTimes.get('M1',[])         
M2_ProcTime = ProcessingTimes.get('M2',[])  

#Call the HandleMissingValues object and replace the missing values in the lists with the mean of the non-missing values
misValues =HandleMissingValues()
M1_ProcTime = misValues.ReplaceWithMean(M1_ProcTime)
M2_ProcTime = misValues.ReplaceWithMean(M2_ProcTime)

MLE = Distributions()      #Call the Distributions object (Maximum Likelihood Estimation - MLE)
KS = DistFittest()      #Call the DistFittest object  (Kolmoghorov-Smirnov test)

M1ProcTime_dist = KS.ks_test(M1_ProcTime)
M2ProcTime_dist = MLE.Normal_distrfit(M2_ProcTime)


#======================= Output preparation: output the updated values in the JSON file of this example ================================#
jsonFile = open('JSON_TwoParallelStations.json','r')      #It opens the JSON file 
data = json.load(jsonFile)                                                              #It loads the file
jsonFile.close()

exportJSON=JSONOutput()
stationId1='St1'
stationId2='St2'
data1=exportJSON.ProcessingTimes(data, stationId1, M1ProcTime_dist)
data2=exportJSON.ProcessingTimes(data1, stationId2, M2ProcTime_dist)
      
jsonFile = open('JSON_ParallelStations_Output.json',"w")     #It opens the JSON file
jsonFile.write(json.dumps(data2, indent=True))                                           #It writes the updated data to the JSON file 
jsonFile.close()                                                                        #It closes the file

#=================== Calling the ExcelOutput object, outputs the outcomes of the statistical analysis in xls files ==========================#
export=Output()

export.PrintStatisticalMeasures(M1_ProcTime,'M1_ProcTime_StatResults.xls')   
export.PrintStatisticalMeasures(M2_ProcTime,'M2_ProcTime_StatResults.xls')

export.PrintDistributionFit(M1_ProcTime,'M1_ProcTime_DistFitResults.xls')
export.PrintDistributionFit(M2_ProcTime,'M2_ProcTime_DistFitResults.xls')
#calls ManPy main script with the input
simulationOutput=ManPyMain.main(input_data=json.dumps(data))
# save the simulation output
jsonFile = open('ManPyOutput.json',"w")     #It opens the JSON file
jsonFile.write(simulationOutput)                                           #It writes the updated data to the JSON file 
jsonFile.close()                                                                        #It closes the file

