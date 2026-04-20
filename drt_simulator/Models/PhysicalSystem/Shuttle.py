import copy

from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import numpy as np

INF = float('inf')
# 다른 원자 모델들과는 다르게 셔틀 객체는 저장된 셔틀의 수 만큼 만들어낸다. 자세한 내용은 Mobility_sim.py 마지막 부분에 있다.
class Shuttle(DEVSAtomicModel):
    
    def __init__(self, strID, globalVar, boardingTime):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["IDLE", "MOVE", "BOARD"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("Schedule")

        # output Ports
        self.addOutputPort("Transit")
        
        # self variables
        self.addStateVariable("strID", strID)

        # variables
        self.moveTime = 0
        self.boardingTime = boardingTime
    
    def detect_position_changes(self, current_list, new_list):
        changed_items = []
        for i, item in enumerate(current_list):
            if i >= len(new_list) or item != new_list[i]:
                changed_items.append(item)
        
        changed_psgr = set(item[2] for item in changed_items)
        
        return changed_psgr
    
    

    # Schedule port로 승객을 태우기 위해 차량이 어떤 경로를 이동할 것인지 그리고 태운 후 어떤 경로로 이동할 것 인지에 대해 업데이트 해주는 로직이다. 
    # 이러한 과정에서 승객의 예상 대기 시간과 도착 시간을 갱신하고, 경로가 몇 번 바뀌었는지 기록한다.
    # 이러한 로직의 결과로 state= Move로 변한다. 
    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "Schedule":
            #def getStateValue(self, varState):
            #   return self.states[varState]
            # states={"strID":strID}
            if self.getStateValue("strID") == objEvent.shuttleID:
                schedule = objEvent
                shuttle = self.globalVar.getShuttleInfoByID(schedule.shuttleID)
                psgr = self.globalVar.getPsgrInfoByID(schedule.psgrID)

                #def setExpectedTime(self, expectedWatingTime, expectedArrivalTime):
                #   self.expectedWatingTime = expectedWatingTime
                #   self.expectedArrivalTime = expectedArrivalTime
                # 예측 대기 시간과 도착 시간을 받아서 각각 저장한다.
                psgr.setExpectedTime(schedule.newPsgrWaitTime,schedule.newPsgrArrivalTime)
                expectedwaitingtime = schedule.newPsgrWaitTime
                expectedarrivaltime = schedule.newPsgrArrivalTime

                waitstarttime = psgr.waitingStartTime
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, psgr.psgrID, {"expectedwaitingtime" :expectedwaitingtime})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, psgr.psgrID, {"expectedarrivaltime" :expectedarrivaltime})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, psgr.psgrID, {"waitstarttime" :waitstarttime})
                else:
                    pass
                self.globalVar.printTerminal("[{}][{}] recevied SCHEDULE{}".format(self.getTime(), self.getStateValue("strID"), schedule.scheduleID))
                
                # 셔틀이 이동하는 동안 경로가 변경되었을 때, 영향을 받는 승객들(탑승중 or 탑승 예정)의 경로 변경 횟수를 추적하는 역할 
                changed_psgr = self.detect_position_changes(shuttle.curDst, schedule.dstLst)
                for i in changed_psgr:
                    psgr = self.globalVar.getPsgrInfoByID(i)
                    psgr.plusPath()
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, i, {'pathChanged': psgr.pathChanged})
                    else:
                        pass

                shuttle.setDstLst(schedule.dstLst)
                shuttle.setPath(schedule.totalPath)
                shuttle.setSchedule(schedule)

                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance() #이벤트 무시 
            return True
        else :
            print("ERROR at Generator ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False


    def funcOutput(self):
        # MOVE 상태는 스케줄을 받은 경우 해당 상태로 천이하게 된다.
        if self.state == "MOVE":          
            #이동 시키려는 특정 셔틀의 상태를 "MOVE" 로 변경 
            shuttle = self.globalVar.getShuttleInfoByID(self.getStateValue("strID"))
            shuttle.setState("MOVE")
            graphInfo = self.globalVar.graphInfo

            #curPath 리스트를 확인하여, 이동할 경로가 남아 있는지 확인
            #이동 시간이 graphInfo에 저장된 데이터에서 가져와 설정됨
            if len(shuttle.curPath) > 1:
                self.moveTime = graphInfo[shuttle.curPath[0]]['links'][shuttle.curPath[1]]['time']
                current_node = shuttle.curPath[0]

                #셔틀 도착시 arrived 메시지 출력 
                if shuttle.curNode == shuttle.curDst[0][0]:  
                    self.globalVar.printTerminal("[{}][{}] arrived #{} for #{} ".format(self.getTime(), self.getStateValue("strID"), shuttle.curNode, shuttle.curDst[0][1]))
                else :
                    self.globalVar.printTerminal("[{}][{}] moved from #{} to #{} [Next Stop : #{}]".format(self.getTime(), self.getStateValue("strID"), shuttle.curPath[0], shuttle.curPath[1],shuttle.curDst[0][0]))
                    #동적 노드 삭제 처리 
                    if current_node.startswith('dynamic_'):
                        # 동적 노드 삭제
                        self.globalVar.remove_dynamic_node(current_node)
            
            shuttle.setActivationTime(shuttle.schedule.scheduleID, self.moveTime)
            shuttle.setPsgrLoad(shuttle.curPsgrNum, self.moveTime)
            shuttle.shuttleID = self.getStateValue("strID")
            # print(shuttle.curDst)
            # vi_shuttle = {}
            # vi_shuttle['shuttle_id'] = self.getStateValue("strID")
            # vi_shuttle['curNode'] = shuttle.curNode
            # vi_shuttle['curPath'] = shuttle.curPath
            # vi_shuttle['curDst'] = shuttle.curDst
            # vi_shuttle['curPsgr'] = shuttle.curPsgr
            
            if self.globalVar.isDBsave == True:
                currenttime = self.getTime()
                state = shuttle.strState
                curNode = shuttle.curNode
                curPath = shuttle.curPath
                curDst = shuttle.curDst
                curPsgr = [passenger.psgrID for passenger in shuttle.curPsgr]
                curPsgrNum = shuttle.curPsgrNum
                self.kpi_saver.vehicle_data(self.globalVar.scenarioID, currenttime, shuttle.shuttleID, state, curDst, curNode, curPath, curPsgr, curPsgrNum)
            else:
                pass
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, currenttime)
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, state), 
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID. curDst),
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, curNode)
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, curPath)
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID. curPsgr)
            
            # self.addOutputEvent("CurPath", vi_shuttle)
            return True
        elif self.state == "BOARD":
            shuttle = self.globalVar.getShuttleInfoByID(self.getStateValue("strID"))
            shuttle.setState("BOARD")
            if shuttle.curDst[0][1] == "BOARDING":
                self.globalVar.printTerminal("[{}][{}] boarded passengers at #{} ".format(self.getTime(), self.getStateValue("strID"), shuttle.curNode))
            else:
                self.globalVar.printTerminal("[{}][{}] dropped off passengers at #{} ".format(self.getTime(), self.getStateValue("strID"), shuttle.curNode))
            dstPsgr = shuttle.curDst[0][2]

            # ["Shuttle1", [101, 102, 103]] : "Shuttle1"에서 승객 101, 102, 103번이 탑승 또는 하차했다는 정보를 시스템에 알린다. 
            self.addOutputEvent("Transit", [self.getStateValue("strID"), dstPsgr])
            shuttle.delDst()
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        shuttle = self.globalVar.getShuttleInfoByID(self.getStateValue("strID"))
        if self.state == "MOVE":
            if shuttle.curNode == shuttle.curDst[0][0]:
                 self.state = self.stateList[2]
            elif len(shuttle.curPath) > 1:
                self.state = self.stateList[1]
                shuttle.setPath(shuttle.curPath[1:])
                shuttle.setNode(shuttle.curPath[0])
                shuttle.setCoordinates(self.globalVar.getNodeInfoByID(shuttle.curPath[0]))
        elif self.state == "BOARD":
            if len(shuttle.curPath) > 1:
                if shuttle.curNode == shuttle.curDst[0][0]: 
                    self.state = self.stateList[2]
                else :
                    self.state = self.stateList[1]
            else:
                shuttle.setState("WAIT")
                shuttle.setPath([])
                self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "MOVE":
            return self.moveTime
        elif self.state == "BOARD":
            return self.boardingTime
        else:
            return 999999999999

