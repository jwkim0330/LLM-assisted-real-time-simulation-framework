from SimulationEngine.Utility.Configurator import Configurator
import json

class EnvironmentLoader:
    def __init__(self, strPath, lstFileNames):
        objConfiguration = Configurator()

        for fName in lstFileNames:
            strFileName = strPath + fName + ".json"
            print("\nLoading "+ strFileName)
            
            with open(strFileName) as json_file:
                objData = json.load(json_file)
                if objData["fileName"] == "shuttleInfo":
                    objConfiguration.addConfiguration("shuttleInfo", objData["shuttleInfo"])
                elif objData["fileName"] == "passengerInfo":
                    objConfiguration.addConfiguration("validGridList", objData["validGridList"])
                    objConfiguration.addConfiguration("validGridWeight", objData["validGridWeight"])            
                    objConfiguration.addConfiguration("stopInfo", objData["stopInfo"])              
                elif objData["fileName"] == "setup":
                    objConfiguration.addConfiguration("monteCarlo", objData["monteCarlo"])
                    objConfiguration.addConfiguration("isShuttleChange", objData["isShuttleChange"])
                    objConfiguration.addConfiguration("numShuttles", objData["numShuttles"])
                    objConfiguration.addConfiguration("psgrStart", objData["psgrStart"])
                    objConfiguration.addConfiguration("psgrEnd", objData["psgrEnd"])
                    objConfiguration.addConfiguration("isTerminalOn", objData["isTerminalOn"])
                    objConfiguration.addConfiguration("isVisualizerOn", objData["isVisualizerOn"])
                    objConfiguration.addConfiguration("isShowFigure", objData["isShowFigure"])
                    objConfiguration.addConfiguration("isSaveFigure", objData["isSaveFigure"])             
                    objConfiguration.addConfiguration("renderTime", objData["renderTime"])
                    objConfiguration.addConfiguration("simulationMode", objData["simulationMode"])
                    objConfiguration.addConfiguration("EDServiceRateLst", objData["EDServiceRateLst"])
                    objConfiguration.addConfiguration("genEndTime", objData["genEndTime"])
                    objConfiguration.addConfiguration("psgrPercentLst", objData["psgrPercentLst"])
                    objConfiguration.addConfiguration("isDBsave", objData["isDBsave"])
                    
                elif objData["fileName"] == "map_graph":
                    graph_data = objData
                    integrated_graph_data = {}

                    for node in graph_data['nodes']:
                        node_id = node['id']
                        integrated_graph_data[node_id] = {
                            'neighbors': set(),
                            'links': {}
                        }

                    for edge in graph_data['links']:
                        source = edge['source']
                        target = edge['target']

                        integrated_graph_data[source]['neighbors'].add(target)
                        integrated_graph_data[target]['neighbors'].add(source)

                        link_key = (source, target)
                        integrated_graph_data[source]['links'][target] = {
                            'max_spd': edge['max_spd'],
                            'length': edge['length'],
                            'time': edge['time'],
                            'vector': edge['vector']
                        }

                        link_key_reverse = (target, source)
                        integrated_graph_data[target]['links'][source] = {
                            'max_spd': edge['max_spd'],
                            'length': edge['length'],
                            'time': edge['time'],
                            'vector': edge['vector']
                        }
                        
                    node_data = {}
                    for node in graph_data['nodes']: 
                        node_id = node['id']  
                        node_data[node_id] = (node['coordinates'][0], node['coordinates'][1])

                    objConfiguration.addConfiguration("graph_data", integrated_graph_data)
                    objConfiguration.addConfiguration("node_data", node_data)

                else:
                    print("JSON FILE ERROR\n")
        
        self.objConfiguration = objConfiguration

    def getConfiguration(self):
        return self.objConfiguration