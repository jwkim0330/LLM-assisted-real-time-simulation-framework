#DEVSModel을 기반으로 결합모델 구성 

import sys

from SimulationEngine.ClassicDEVS.DEVSCoupling import DEVSCoupling
from SimulationEngine.ClassicDEVS.DEVSModel import DEVSModel
from SimulationEngine.CouplingGraph import CouplingEdge, CouplingNode
from SimulationEngine.Utility.Logger import Logger

class DEVSCoupledModel(DEVSModel):

    def __init__(self, ID):
        super().__init__()
        self.models = {}
        self.edges = []
        self.nodesWithID = {}
        self.setModelID(ID)

    def addModel(self, model):
        self.models[model.getModelID()] = model
        model.setContainerModel(self)

    def addCoupling(self, srcModel, srcPort, tarModel, tarPort):
        if srcModel.getModelID() + "(" + srcPort + ")" in self.nodesWithID:
            srcNode = self.nodesWithID[srcModel.getModelID() + "(" + srcPort + ")"]
        else:
            srcNode = CouplingNode(srcModel, srcModel.getModelID(), srcPort)
            self.nodesWithID[srcModel.getModelID() + "(" + srcPort + ")"] = srcNode

        if tarModel.getModelID() + "(" + tarPort + ")" in self.nodesWithID:
            tarNode = self.nodesWithID[tarModel.getModelID() + "(" + tarPort + ")"]
        else:
            tarNode = CouplingNode(tarModel, tarModel.getModelID(), tarPort)
            self.nodesWithID[tarModel.getModelID() + "(" + tarPort + ")"] = tarNode

        edge = CouplingEdge(srcNode, tarNode)
        self.edges.append(edge)
        if self.getSimulationEngine() != -1:
            self.getSimulationEngine().getCouplingGraph().addEdge(edge)

    def queryMinTimeAdvance(self):
        minTA = sys.float_info.max
        for modelID in self.models:
            model = self.models[modelID]
            ta = model.queryTimeAdvance()
            if ta < minTA:
                minTA = ta
        self.logger.log(Logger.TA,"Query MIN TA (" + self.getModelID() + ") : " + str(minTA))

        return minTA

    def queryMinTime(self):
        nextTime = sys.float_info.max
        for modelID in self.models:
            model = self.models[modelID]
            time = model.queryTime()
            if time < nextTime:
                nextTime = time
        self.logger.log(Logger.TA,"Query Min Time (" + self.getModelID() + ") : " + str(nextTime))
        return nextTime

    def performOutput(self, currentTime):
        self.time = currentTime
        for modelID in self.models:
            modelNextTime = self.models[modelID].queryTime()
            if modelNextTime <= currentTime:
                isDone = self.models[modelID].performOutput(currentTime)
                if isDone == True:
                    return modelID

    def queryTimeAdvance(self):
        return self.queryMinTimeAdvance()

    def queryTime(self):
        return self.queryMinTime()

    def getModels(self):
        return self.models

    def getCouplingNodes(self):
        return self.nodesWithID

    def getCouplingEdges(self):
        return self.edges

    def addExternalOutputCoupling(self,srcModel,srcPort,tarPort):
        self.addCoupling(srcModel, srcPort, self, tarPort)

    def addExternalInputCoupling(self, srcPort, tarModel, tarPort):
        self.addCoupling(self, srcPort, tarModel, tarPort)

    def addInternalCoupling(self, srcModel, srcPort, tarModel, tarPort):
        self.addCoupling(srcModel, srcPort, tarModel, tarPort)



    def getCoupling(self):
        ret = []
        for edge in self.edges:
            ret.append(DEVSCoupling(edge.srcNode.getModel(), edge.srcNode.getPort(), edge.tarNode.getModel(),
                                    edge.tarNode.getPort()))
        return ret

if __name__ == "__main__":
    pass