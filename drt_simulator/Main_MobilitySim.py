from SimulationEngine.SimulationEngine import SimulationEngine
from Environment.EnvironmentLoader import EnvironmentLoader
from Models.MobilitySim_model import MobilitySim_model
from DataServer import KPIDataSaver
import time
import numpy as np
import pylab
import os

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)

## Load JSON setup Files ##
path = "./JSON/"
files = ["map_graph_with_vectors", "passengerInfo", "shuttleInfo", "setup"] 
objConfiguration = EnvironmentLoader(path, files).getConfiguration()
## Mode selection load ##
simulationMode = objConfiguration.getConfiguration("simulationMode")

## simulation setups load ##
renderTime = objConfiguration.getConfiguration("renderTime")
isShuttleChange = objConfiguration.getConfiguration("isShuttleChange")
monteCarlo = objConfiguration.getConfiguration("monteCarlo")
numShuttles = objConfiguration.getConfiguration("numShuttles")
genEndTime = objConfiguration.getConfiguration("genEndTime")
EDServiceRateLst = objConfiguration.getConfiguration("EDServiceRateLst")
psgrPercentLst = objConfiguration.getConfiguration("psgrPercentLst")
totalSimStart = 0

# 시뮬레이션 시작 전 KPI 테이블 초기화 (passengers_kpi, vehicle_kpi)
kpi_saver = KPIDataSaver()
kpi_saver.delete_all_data()
kpi_saver.disconnect()

## for simulation ##
if simulationMode == True:
    if isShuttleChange == True:
        for EDServiceRate in EDServiceRateLst:
            for psgrPercent in psgrPercentLst:
                for numShuttle in range(1, numShuttles + 1):
                    if monteCarlo == 0:
                        monteCarlo = 1
                    for i in range(1, monteCarlo + 1):
                        if i == 1 and numShuttle == 1:
                            objModels = MobilitySim_model(objConfiguration, path, i, monteCarlo, None, renderTime, numShuttle, numShuttles, isShuttleChange, genEndTime, EDServiceRate, psgrPercent, simulationMode)
                        else:
                            objModels = MobilitySim_model(objConfiguration, path, i, monteCarlo, objModels.prevAnalysisModel, renderTime, numShuttle, numShuttles, isShuttleChange, genEndTime, EDServiceRate, psgrPercent, simulationMode)
                        engine = SimulationEngine()
                        engine.setOutmostModel(objModels)
                        start = time.time()
                        if i == 1 and numShuttle == 1:
                            totalSimStart = start
                        print("\nSimulation Start numShuttle::#{}/{} | ED ServiceRate::#{} | Psgr Percent::#{} | MonteCarlo::#{}/{}".format(numShuttle, numShuttles, EDServiceRate, psgrPercent, i, monteCarlo ))
                        engine.run(maxTime=999999999)
                        print("Simulation End numShuttle::#{}/{} | ED ServiceRate::#{} | Psgr Percent::#{} | MonteCarlo::#{}/{}".format(numShuttle, numShuttles, EDServiceRate, psgrPercent, i, monteCarlo))
                        print("time: {}[s]".format(time.time()-start))
    else:
        for EDServiceRate in EDServiceRateLst:
                for psgrPercent in psgrPercentLst:
                    if monteCarlo == 0:
                        monteCarlo = 1
                    for i in range(1, monteCarlo + 1):
                        if i == 1:
                            objModels = MobilitySim_model(objConfiguration, path, i, monteCarlo, None, renderTime, numShuttles, numShuttles, isShuttleChange, genEndTime, EDServiceRate, psgrPercent, simulationMode)
                        else:
                            objModels = MobilitySim_model(objConfiguration, path, i, monteCarlo, objModels.prevAnalysisModel, renderTime, numShuttles, numShuttles, isShuttleChange, genEndTime, EDServiceRate, psgrPercent, simulationMode)
                        engine = SimulationEngine()
                        engine.setOutmostModel(objModels)
                        start = time.time()
                        if i == 1:  
                            totalSimStart = start
                        print("\nSimulation Start numShuttle::#{} | ED ServiceRate::#{} | Psgr Percent::#{} | MonteCarlo::#{}/{}".format(numShuttles, EDServiceRate, psgrPercent, i, monteCarlo))
                        engine.run(maxTime=999999999)
                        print("Simulation End numShuttle::#{} | ED ServiceRate::#{} | Psgr Percent::#{} | MonteCarlo::#{}/{}".format(numShuttles, EDServiceRate, psgrPercent, i, monteCarlo))
                        print("time: {}[s]".format(time.time()-start))        
    print("\ntotal time: {}[s]".format(time.time()-totalSimStart))
    
