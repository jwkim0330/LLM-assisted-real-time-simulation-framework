# 모델끼리 결합할때 src와 port를 지정하는 클래스
class DEVSCoupling:

    def __init__(self,srcModel,srcPort,tarModel,tarPort):
        self.srcModel = srcModel
        self.srcPort = srcPort
        self.tarModel = tarModel
        self.tarPort = tarPort

    def getSrcModel(self):
        return self.srcModel

    def getTarModel(self):
        return self.tarModel

    def getSrcPort(self):
        return self.srcPort

    def getTarPort(self):
        return self.tarPort

    def __str__(self):
        return self.srcModel.getModelID()+"("+self.srcPort+")"+"->"+self.tarModel.getModelID()+"("+self.tarPort+")"
