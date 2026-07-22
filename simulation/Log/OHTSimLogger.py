import csv
import datetime

current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

class OHTSimLogger:
    def __init__(self, logPath, logVehicle, isLogOn, iter, maxSim, isAnalysisLogOn):
        self.logPath = logPath
        self.maxSim = maxSim
        self.logVehicle = logVehicle
        self.objLog = {}
        self.objWriter = {}
        self.objAnalysisLog = {}
        self.objAnalysisWriter = {}
        self.isLogOn = isLogOn
        self.iter = iter
        self.isAnalysisLogOn = isAnalysisLogOn
        if self.isLogOn == True:
            logName = str(logVehicle)[:-4] + str(self.iter)
            fixedPath = f"{logPath}{logName}_{current_time}.csv"
            self.objLog[logName] = open(fixedPath, "w", newline='')
            self.objWriter[logName] = csv.writer(self.objLog[logName])          

    def __del__(self):
        if self.isLogOn == True:
            if self.objLog is not None:
                for key, value in self.objLog.items():
                    self.objLog[key].close()
            if self.objAnalysisLog is not None:
                for key, value in self.objAnalysisLog.items():
                    self.objAnalysisLog[key].close()

    ## for the simulation data ##
    def addLogDictionarySimulation(self, type, dblTimestep, modelID, dicRecord):
        if self.isLogOn == True:
            tempName = type + str(self.iter)
            lstWrite = []
            lstWrite.append(dblTimestep)
            lstWrite.append(modelID)
            for objKey in dicRecord.keys():
                lstWrite.append(objKey)
                lstWrite.append(dicRecord[objKey])
            self.objWriter[tempName].writerow(lstWrite)
            self.objLog[tempName].flush()

    ## for the simulation data analysis ##
    def addLogDictionaryAnalysis(self, logName, dicRecord):      
        if self.isAnalysisLogOn == True:
            if logName not in self.objAnalysisLog:
                tempPath = logName.split('_')
                fixedPath = f"{self.logPath}results/{tempPath[0]}/{logName}.csv"
                self.objAnalysisLog[logName] = open(fixedPath, "w", newline='')
                self.objAnalysisWriter[logName] = csv.writer(self.objAnalysisLog[logName])
            prevKeyPointer = None
            lstWrite = []
            for objKey in dicRecord.keys():
                idx = objKey.find(']')
                iter = objKey[1:idx]
                if prevKeyPointer == None:
                    prevKeyPointer = iter
                elif prevKeyPointer != iter:
                    prevKeyPointer = iter
                    self.objAnalysisWriter[logName].writerow(lstWrite)
                    lstWrite.clear()
                lstWrite.append(objKey)
                lstWrite.append(dicRecord[objKey])
            if len(lstWrite) != None:
                self.objAnalysisWriter[logName].writerow(lstWrite)
                lstWrite.clear()
            self.objAnalysisLog[logName].flush()

    def setIter(self, iter):
        self.iter = iter
        if self.isLogOn == True:
            if self.objLog is not None:
                for key, value in self.objLog.items():
                    self.objLog[key].close()
                self.objLog.clear()
                self.objWriter.clear()
                logName = str(self.logVehicle)[:-4] + str(self.iter)
                fixedPath = f"{self.logPath}{logName}_{current_time}.csv"
                self.objLog[logName] = open(fixedPath, "w", newline='')
                self.objWriter[logName] = csv.writer(self.objLog[logName])
        if self.isAnalysisLogOn == True:
            for key, value in self.objAnalysisLog.items():
                self.objAnalysisLog[key].close()
            self.objAnalysisLog.clear()
            self.objAnalysisWriter.clear()