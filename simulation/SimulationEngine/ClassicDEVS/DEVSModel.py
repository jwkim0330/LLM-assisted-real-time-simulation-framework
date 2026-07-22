# 모델을 표현하는 기본 구조, 여기서는 기본적인 정보들을 클래스로 구현하여 초기화 시켜 놓았다. 
# 모델을 구현하는데에 있어서 필요한 모든 요소를 정의 해놓았고, 필요할 때 해당 모듈을 가져와서 사용하는 것 같다. 



from SimulationEngine.Visualzer.Visualizer import VisualNode, VisualEdge

class DEVSModel:

    engine = -1

    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.states = {}
        self.visualNodes = []
        self.visualEdges = []
        self.containerModel = None #devs 모델을 포함하는 상위 모델이라고 한다, 코드 분석을 더 해볼 필요가 존재한다. 아직 확실히 아는 것은 아님 

    def setContainerModel(self, model):
        self.containerModel = model
    def getContainerModel(self):
        return self.containerModel

    def setModelID(self, ID):
        self.ID = ID
    def getModelID(self):
        return self.ID

    def addInputPort(self, varInput):
        self.inputs.append(varInput)
    def getInputPorts(self):
        return self.inputs
    def removeInputPort(self, varInput):
        self.inputs.remove(varInput)

    def addOutputPort(self, varOutput):
        self.outputs.append(varOutput)
    def getOutputPorts(self):
        return self.outputs
    def removeOutputPort(self, varOutput):
        self.outputs.remove(varOutput)

    def addStateVariable(self, varState, varStateValue):
        self.states[varState] = varStateValue
    def setStateValue(self, varState, varStateValue):
        self.states[varState] = varStateValue    
    def getStates(self):
        return self.states
    def getStateValue(self, varState):
        return self.states[varState]
    def removeStateVariable(self, varState):
        self.states.remove(varState)

    def setSimulationEngine(self, engine):
        self.engine = engine
    def getSimulationEngine(self):
        return self.engine

    def setTime(self, currentTime):
        self.time = currentTime
    def getTime(self):
        return self.engine.getTime()

    def setLogger(self, logger):
        self.logger = logger

    def addVisualizeNode(self, name, x, y, size, color):
        self.visualNodes = [VisualNode(name, x, y, size, color)]
    def getVisualNodes(self):
        return self.visualNodes
    def removeVisualNodes(self):
        self.visualNodes = []

    def addVisualizeEdge(self, srcName, tarName):
        self.visualEdges = [VisualEdge(srcName, tarName)]
    def getVisualEdges(self):
        return self.visualEdges
    def removeVisualEdges(self):
        self.visualEdges = []

if __name__ == "__main__":
    pass