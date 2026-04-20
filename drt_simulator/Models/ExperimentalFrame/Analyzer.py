from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import copy
import numpy as np
import psycopg2
import json
import matplotlib
import datetime
import random
import os

matplotlib.rcParams['figure.max_open_warning'] = 40  
current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    
class Analyzer(DEVSAtomicModel):
    def __init__(self, strID, globalVar, psgrStart, psgrEnd, iter, maxSim, numShuttle, maxShuttle, isShowFigure, isSaveFigure, isShuttleChange, EDService, EDServiceRate, psgrPercent):
        super().__init__(strID)

        self.save_folder = os.path.join('KPI', f'KPI_{EDServiceRate}_{psgrPercent}_{current_time}')
        os.makedirs(self.save_folder, exist_ok=True)
        
        # set Global Variables
        self.globalVar = globalVar
        self.iter = iter
        self.maxSim = maxSim
        self.numShuttle = numShuttle
        self.maxShuttle = maxShuttle
        self.isShowFigure = isShowFigure
        self.isSaveFigure = isSaveFigure
        self.isShuttleChange = isShuttleChange
        
        self.EDServiceRate = EDServiceRate
        
        if self.EDServiceRate == 0:
            self.EDService = False
        else :
            self.EDService = True


        self.colorList = ['red', 'tomato', 'sienna', 'saddlebrown', 'green',\
                         'darkgreen', 'lime', 'teal', 'blue', 'darkblue',\
                         'rebeccapurple', 'royalblue', 'cyan', 'dodgerblue', 'darkslategrey',\
                         'magenta', 'mediumvioletred', 'yellow', 'darkolivegreen', 'black',\
                         'gold', 'lightcoral', 'indianred', 'coral', 'orangered',\
                         'crimson', 'darkkhaki', 'steelblue', 'rosybrown', 'indigo']
        self.gradientColorList = ['green', 'darkgreen', 'lime',  'gold', 'yellow', 'lightcoral', 'indianred', 'coral', 'tomato', 'orangered', 'red']
        # states
        self.stateList = ["WAIT", "ANALYSIS"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("SimumlationComplete")

        # output Ports

        # self variables
        self.addStateVariable("strID", strID)
        self.addStateVariable("intpsgrStart", psgrStart)
        self.addStateVariable("intpsgrEnd", psgrEnd)
        
        
        ## passenger View ##
        self.dictPsgrWaitTime = {}
        self.dictPsgrBoardingTime = {}
        self.dictPsgrWaitTimeGap = {}
        self.dictPsgrBoardingTimeGap = {}
        self.dictAcceptanceRate = {}
        
        ## ed service View ##
        self.dictLightPsgrWaitTime = {}
        self.dictLightPsgrBoardingTime = {}
        self.dictLightPsgrWaitTimeGap = {}
        self.dictLightPsgrBoardingTimeGap = {}
        self.dictLightAcceptanceRate = {}
        self.dictEDSPsgrWaitTime = {}
        self.dictEDSPsgrBoardingTime = {}
        self.dictEDSPsgrWaitTimeGap = {}
        self.dictEDSPsgrBoardingTimeGap = {}
        self.dictEDSAcceptanceRate = {}
        
        ## shuttle View ##
        self.dictShuttleUtilizationRate = {}
        self.dicShuttleLoad = {}
        
        ## passenger View ##
        self.totaldictPsgrWaitTime = {}
        self.totaldictPsgrBoardingTime = {}
        self.totaldictPsgrWaitTimeGap = {}
        self.totaldictPsgrBoardingTimeGap = {}
        self.totaldictAcceptanceRate = {}
        
        ## shuttle View ##
        self.totaldictShuttleUtilizationRate = {}
        self.totaldicShuttleLoad = {}
        
        ## ed service View ##
        self.totaldictLightPsgrWaitTime = {}
        self.totaldictLightPsgrBoardingTime = {}
        self.totaldictLightPsgrWaitTimeGap = {}
        self.totaldictLightPsgrBoardingTimeGap = {}
        self.totaldictLightAcceptanceRate = {}
        self.totaldictEDSPsgrWaitTime = {}
        self.totaldictEDSPsgrBoardingTime = {}
        self.totaldictEDSPsgrWaitTimeGap = {}
        self.totaldictEDSPsgrBoardingTimeGap = {}
        self.totaldictEDSAcceptanceRate = {}
        

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "SimumlationComplete":
            self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Analyzer ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "ANALYSIS":
            
            psgrStart = self.getStateValue("intpsgrStart")
            psgrEnd = self.getStateValue("intpsgrEnd")
            
            arrivalQueue, failQueue = self.globalVar.getEndPsgr()
            self.psgrKPI(arrivalQueue, psgrStart, psgrEnd, self.EDService)
  
            if self.EDService :
                failEDS = 0
                failLight = 0
                acceptEDS = 0
                acceptLight = 0
                
                for key, psgr in failQueue.items():
                    if psgr.psgrEDS:
                        failEDS += 1
                    else :
                        failLight += 1
                for key, psgr in arrivalQueue.items():
                    if psgr.psgrEDS:
                        acceptEDS += 1
                    else :
                        acceptLight += 1
                if (acceptLight+failLight) != 0:
                    self.dictLightAcceptanceRate[self.iter] = acceptLight/(acceptLight+failLight)*100
                if (acceptEDS+failEDS) != 0:
                    self.dictEDSAcceptanceRate[self.iter] = acceptEDS/(acceptEDS+failEDS)*100
            else:
                if (len(arrivalQueue)+len(failQueue)) != 0:
                    self.dictAcceptanceRate[self.iter] = len(arrivalQueue)/(len(arrivalQueue)+len(failQueue))*100
            
            shuttleInfo = self.globalVar.getShuttleInfo()
            self.shuttleKPI(shuttleInfo)
            
            kpi_data = {
                'psgrWaitTime': self.dictPsgrWaitTime,
                'psgrBoardingTime': self.dictPsgrBoardingTime,
                'psgrWaitTimeGap': self.dictPsgrWaitTimeGap,
                'psgrBoardingTimeGap': self.dictPsgrBoardingTimeGap,
                'acceptanceRate': self.dictAcceptanceRate,
                'shuttleUtilizationRate': self.dictShuttleUtilizationRate,
                'shuttleLoad': self.dicShuttleLoad
            }


            if self.iter == self.maxSim:             
                if self.EDService :
                    self.totaldictLightPsgrWaitTime[self.numShuttle] = copy.deepcopy(self.dictLightPsgrWaitTime)
                    self.totaldictLightPsgrBoardingTime[self.numShuttle] = copy.deepcopy(self.dictLightPsgrBoardingTime)
                    self.totaldictLightPsgrWaitTimeGap[self.numShuttle] = copy.deepcopy(self.dictLightPsgrWaitTimeGap)
                    self.totaldictLightPsgrBoardingTimeGap[self.numShuttle] = copy.deepcopy(self.dictLightPsgrBoardingTimeGap)
                    self.totaldictLightAcceptanceRate[self.numShuttle] = copy.deepcopy(self.dictLightAcceptanceRate)
                    
                    self.totaldictEDSPsgrWaitTime[self.numShuttle] = copy.deepcopy(self.dictEDSPsgrWaitTime)
                    self.totaldictEDSPsgrBoardingTime[self.numShuttle] = copy.deepcopy(self.dictEDSPsgrBoardingTime)
                    self.totaldictEDSPsgrWaitTimeGap[self.numShuttle] = copy.deepcopy(self.dictEDSPsgrWaitTimeGap)
                    self.totaldictEDSPsgrBoardingTimeGap[self.numShuttle] = copy.deepcopy(self.dictEDSPsgrBoardingTimeGap)
                    self.totaldictEDSAcceptanceRate[self.numShuttle] = copy.deepcopy(self.dictEDSAcceptanceRate)

                    self.totaldictShuttleUtilizationRate[self.numShuttle] = copy.deepcopy(self.dictShuttleUtilizationRate)
                    self.totaldicShuttleLoad[self.numShuttle] = copy.deepcopy(self.dicShuttleLoad)
                

                    self.dictLightPsgrWaitTime.clear()
                    self.dictLightPsgrBoardingTime.clear()
                    self.dictLightPsgrWaitTimeGap.clear()
                    self.dictLightPsgrBoardingTimeGap.clear()
                    self.dictLightAcceptanceRate.clear()
                    
                    self.dictEDSPsgrWaitTime.clear()
                    self.dictEDSPsgrBoardingTime.clear()
                    self.dictEDSPsgrWaitTimeGap.clear()
                    self.dictEDSPsgrBoardingTimeGap.clear()
                    self.dictEDSAcceptanceRate.clear()
                    
                    self.dictShuttleUtilizationRate.clear()
                    self.dicShuttleLoad.clear()
                    
                else:
                    self.totaldictPsgrWaitTime[self.numShuttle] = copy.deepcopy(self.dictPsgrWaitTime)
                    self.totaldictPsgrBoardingTime[self.numShuttle] = copy.deepcopy(self.dictPsgrBoardingTime)
                    self.totaldictPsgrWaitTimeGap[self.numShuttle] = copy.deepcopy(self.dictPsgrWaitTimeGap)
                    self.totaldictPsgrBoardingTimeGap[self.numShuttle] = copy.deepcopy(self.dictPsgrBoardingTimeGap)
                    self.totaldictAcceptanceRate[self.numShuttle] = copy.deepcopy(self.dictAcceptanceRate)
                    
                    self.totaldictShuttleUtilizationRate[self.numShuttle] = copy.deepcopy(self.dictShuttleUtilizationRate)
                    self.totaldicShuttleLoad[self.numShuttle] = copy.deepcopy(self.dicShuttleLoad)


                    self.dictPsgrWaitTime.clear()
                    self.dictPsgrBoardingTime.clear()
                    self.dictPsgrWaitTimeGap.clear()
                    self.dictPsgrBoardingTimeGap.clear()
                    self.dictAcceptanceRate.clear()
                    
                    self.dictShuttleUtilizationRate.clear()
                    self.dicShuttleLoad.clear()
    
            self.globalVar.printTerminal("[{}][{}] Analysis complete".format(self.getTime(), self.getStateValue("strID")))           
            return True
        else:
            print("ERROR at Analyzer OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "ANALYSIS":
            self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Analyzer InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "ANALYSIS":
            return 0
        else:
            return 999999999999

    def psgrKPI(self, arrivalQueue, psgrStart, psgrEnd, EDService):
        if EDService :
            dictLightPsgrWaitTime = {}
            dictLightPsgrBoardingTime = {}
            dictLightPsgrWaitTimeGap = {}
            dictLightPsgrBoardingTimeGap = {}
            dictEDSPsgrWaitTime = {}
            dictEDSPsgrBoardingTime = {}
            dictEDSPsgrWaitTimeGap = {}
            dictEDSPsgrBoardingTimeGap = {}
            
            for key, value in arrivalQueue.items():
                psgrID = int(key)
                if psgrID >= psgrStart and psgrID <= psgrEnd:
                    if value.psgrEDS:  
                        dictEDSPsgrWaitTime[key] = value.departureTime - value.waitingStartTime
                        dictEDSPsgrBoardingTime[key] = value.arrivalTime - value.departureTime
                        dictEDSPsgrWaitTimeGap[key] = value.departureTime - value.waitingStartTime - value.expectedWatingTime
                        dictEDSPsgrBoardingTimeGap[key] = value.arrivalTime - value.departureTime - value.expectedArrivalTime
                    else:  
                        dictLightPsgrWaitTime[key] = value.departureTime - value.waitingStartTime
                        dictLightPsgrBoardingTime[key] = value.arrivalTime - value.departureTime
                        dictLightPsgrWaitTimeGap[key] = value.departureTime - value.waitingStartTime - value.expectedWatingTime
                        dictLightPsgrBoardingTimeGap[key] = value.arrivalTime - value.departureTime - value.expectedArrivalTime


            self.dictLightPsgrWaitTime[self.iter] = dictLightPsgrWaitTime
            self.dictLightPsgrBoardingTime[self.iter] = dictLightPsgrBoardingTime
            self.dictLightPsgrWaitTimeGap[self.iter] = dictLightPsgrWaitTimeGap
            self.dictLightPsgrBoardingTimeGap[self.iter] = dictLightPsgrBoardingTimeGap

            self.dictEDSPsgrWaitTime[self.iter] = dictEDSPsgrWaitTime
            self.dictEDSPsgrBoardingTime[self.iter] = dictEDSPsgrBoardingTime
            self.dictEDSPsgrWaitTimeGap[self.iter] = dictEDSPsgrWaitTimeGap
            self.dictEDSPsgrBoardingTimeGap[self.iter] = dictEDSPsgrBoardingTimeGap

                
            
        else:
            dictPsgrWaitTime = {}
            dictPsgrBoardingTime = {}
            dictPsgrWaitTimeGap = {}
            dictPsgrBoardingTimeGap = {}
            for key, value in arrivalQueue.items():
                psgrID = int(key)
                if psgrID >= psgrStart and psgrID <= psgrEnd: 
                    dictPsgrWaitTime[key] = value.departureTime - value.waitingStartTime
                    dictPsgrBoardingTime[key] = value.arrivalTime - value.departureTime
                    dictPsgrWaitTimeGap[key] = value.departureTime - value.waitingStartTime - value.expectedWatingTime
                    dictPsgrBoardingTimeGap[key] = value.arrivalTime - value.departureTime - value.expectedArrivalTime
            self.dictPsgrWaitTime[self.iter] = dictPsgrWaitTime
            self.dictPsgrBoardingTime[self.iter] = dictPsgrBoardingTime
            self.dictPsgrWaitTimeGap[self.iter] = dictPsgrWaitTimeGap
            self.dictPsgrBoardingTimeGap[self.iter] = dictPsgrBoardingTimeGap
            
        
            

    def shuttleKPI(self, shuttleInfo):
        dictShuttleUtilizationRate = {}
        simTime = self.getTime()
        
        for key, value in shuttleInfo.items():
            temptime = 0
            for _, value in value.dictActivationTime.items(): 
                temptime = temptime+value
            dictShuttleUtilizationRate[key] = temptime/simTime
        self.dictShuttleUtilizationRate[self.iter] = dictShuttleUtilizationRate
        
        dicShuttleLoad = {}
        for key, value in shuttleInfo.items():
            if len(value.dictPsgrLoad) == 0:
                continue  
            psgrSum = 0
            timeSum = 0
            for psgrCnt, time in value.dictPsgrLoad.items():
                if psgrCnt != 0: 
                    psgrSum += time * psgrCnt
                    timeSum += time
            if timeSum > 0:
                dicShuttleLoad[key] = psgrSum / timeSum
            else:
                dicShuttleLoad[key] = 0 
        self.dicShuttleLoad[self.iter] = dicShuttleLoad

    def setSimulationIteration(self, iter):
        self.iter = iter
    def setShuttleIteration(self, numShuttle):
        self.numShuttle = numShuttle
    def setGlobalVar(self, globalVar):
        self.globalVar = globalVar

    def getCurrentTime(self):
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        
        
