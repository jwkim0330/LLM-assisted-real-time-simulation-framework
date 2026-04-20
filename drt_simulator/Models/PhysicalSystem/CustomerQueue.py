import random
from DataServer import KPIDataSaver
from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel

INF = float('inf')

 
#Transit은 shuttle 원자 모델에서 customerQueue 원자 모델로 보낸 Event 객체, 
#Transit 값이 전달되는 경우는 "특정 셔틀에 승객이 탑승하거나 내린 순간" 이다.
#objEvent 는 Event 객체로 구성되고, 우리가 접근하려는 데이터는 Event.message로 접근 가능하다.  
#실제 Event.meaage 데이터는 다음과 같다. 
#["Shuttle1", [101, 102, 103]]  : shuttle name , 탑승 또는 하차 승객 psgrID 
#"Shuttle1"에서 승객 101, 102, 103번이 탑승 또는 하차했다는 정보를 시스템에 알린다.
class CustomerQueue(DEVSAtomicModel):
    # devs 모델의 id, 전역 변수를 받는다. 
    def __init__(self, strID, globalVar):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["WAIT", "CALL", "TRANSIT", "ANALYSIS"]
        self.state = self.stateList[0]

        # input Ports, inputs=[] 에 str 형식으로 저장 -> 이걸 어떻게 끌어올것인가> 이게 관건, 
        # 한편, Trasit 이 무엇인지 파악하는 것이 중요 
        # def addInputPort(self, varInput):
        #   self.inputs.append(varInput) 
        # self.inputs=['Passenger','Transit']

        self.addInputPort("Passenger")
        self.addInputPort("Transit")

        # output Ports
        # 각각이 의미하는 바가 무엇인지 파악하는 것이 중요
        #  self.ouputs=['Call','SimulationComplete,Call_vi'] 
        self.addOutputPort("Call")
        self.addOutputPort("SimumlationComplete")
        
        

        # self variables
        #def addStateVariable(self, varState, varStateValue):
        #   self.states[varState] = varStateValue
        # self.states = {"strID": strID} 여기서 들어 가게 될 strId는 무엇인지 파악 
        self.addStateVariable("strID", strID)
   
        # variables
        self.passengerlst = [] #승객 리스트, 호출은 했지만 아직 처리되지 못한 승객이 기다리는 곳 (generator에서 온 값)
        self.transitlst = [] # 아마 shuttle에서 전달된 transit값이 저장되는 큐이다. 
        self.endPsgr = 0 
        self.simDone = False


    # MobilitySim_model.py에서 addCoupling을 통해 다른 객체와 연결 1. generator 2. shuttle 
    # 2가지 객체가 해당 함수에 전달된다. 1. Passenger 객체(generator) 2.  Transit 객체(shuttle)
    def funcExternalTransition(self, strPort, objEvent):
        #generator에서 전달한 Passenger객체 
        if strPort == "Passenger":
            self.passengerlst.append(objEvent)
            if self.state == "WAIT": #만약 현재 상태가 wait 상태로 대기중이라면 call 상태로 천이(하여 차량을 호출하라,이 부분은 추측 아마 하지 않을까?) 
                self.state = self.stateList[1]
            else:
                #def continueTimeAdvance(self):
                #   self.blnContinue = True -> DEVS 시뮬레이션에서 외부 이벤트 발생 시 Time Advance를 강제로 즉각 발생시키기 위한 플래그
                # 만약 상태가 wait 이 아니라면 time Advance를 발생 -아직 이해 부족, wait이 아닌 경우 다른 상태겠지, 이러한 상황에서 바로 시뮬레이션을 실행하라는건가? 뭐지?
                self.continueTimeAdvance()
            return True
        #Transit은 shuttle 원자 모델에서 customer queue로 보낸 객체, 특정 셔틀에 승객이 탑승하거나 내린 경우 해당 객체를 Event 객체 형식으로 보내게 된다.
        # objEvent 형식은 다음과 같다  ["Shuttle1", [101, 102, 103]] : "Shuttle1"에서 승객 101, 102, 103번이 탑승 또는 하차했다는 정보를 시스템에 알린다.    
        elif strPort == "Transit":
            self.transitlst.append(objEvent)
            if self.state == "WAIT": # wait 상태라면 transit 상태로 천이하여 해야할 일을 하라 
                self.state = self.stateList[2]
            else:
                self.continueTimeAdvance()
        else:
            print("ERROR at MainController ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False


    def funcOutput(self): #output을 산출하는 상태 : CALL, TRANSIT, ANALYSIS cf wait은 산출x 
        # call 상태는 wait 상태에서 호출이 있는 경우 천이하는 위치 
        if self.state == "CALL":
            currentPsgrId = self.passengerlst[0] # 먼저 온 승객 처리 
            self.addOutputEvent("Call", currentPsgrId) # call eventqueue에 currentPsgrID 라는 승객 객체를 전달 
            
            #def getPsgrInfoByID(self, psgrID):
                #psgr = None
                #if psgrID in self.psgrWaitingQueue:
                #    psgr = self.psgrWaitingQueue[psgrID]
                #   Waitingqueue는 딕셔너리 ,self.psgrWaitingQueue[psgrID] = Passenger(psgrID, psgrNum, DNode, ANode, psgrEDS, time) 

                #elif psgrID in self.psgrRidingQueue:
                #    psgr = self.psgrRidingQueue[psgrID]

                #elif psgrID in self.psgrArrivalQueue:
                #    psgr = self.psgrArrivalQueue[psgrID]

                #elif psgrID in self.psgrFailQueue:
                #    psgr = self.psgrFailQueue[psgrID]

                #else:
                #    print("psgrID is not existe")
                #return psgr
            # generator에서 승객을 생성 후 psgrWaitingQueue를 만들어서 key:승객id value:Passenger 객체 를 저장해놓았고 그에 대한 승객 객체를 wait 상태로 천이 (default가 wait이긴 하다.) 
            psgr = self.globalVar.getPsgrInfoByID(currentPsgrId)

            #def setTime(self, currentTime):
                #self.time = currentTime
            psgr.setTime("WAIT", self.getTime())
            self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} called shuttle #{} to #{}".format(self.getTime(), self.getStateValue("strID"), psgr.psgrID,psgr.psgrNum,psgr.strDepartureNode,psgr.strArrivalNode))
            self.passengerlst.pop(0) #처리한 승객은 list에서 제거 
            return True
        elif self.state == "TRANSIT":
            ## ["Shuttle1", [101, 102, 103]] 이러한 정보가 transitlist 하나의 요소이다. 
            transitInfo = self.transitlst[0]
            if str(type(transitInfo)) != "<class 'int'>" :
                targetShuttleID = transitInfo[0]
                targetPsgr = self.globalVar.getPsgrInfoByID(int(transitInfo[1]))
                targetShuttle = self.globalVar.getShuttleInfoByID(targetShuttleID)
                if targetPsgr.strState == "WAIT":
                    targetShuttle.adjustPsgr(targetPsgr,targetPsgr.psgrNum)
                    self.globalVar.setRidePsgr(targetPsgr.psgrID)
                    targetPsgr.setPsgrShuttle(targetShuttleID)
                    targetPsgr.setTime("DEPARTURE", self.getTime())
                    targetPsgr.setState("BOARDING")
                    boardingtime = self.getTime()
                    success = True
                    shuttleID = targetShuttleID
                    dep_node = targetPsgr.strDepartureNode
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'boardingtime' : boardingtime})
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'success' : success})
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'shuttleID' : shuttleID})
                    else:
                        pass
                    self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} board {} #{} to #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.psgrNum,targetShuttleID, targetPsgr.strDepartureNode,targetPsgr.strArrivalNode))
                elif targetPsgr.strState == "BOARDING":
                    targetShuttle.adjustPsgr(targetPsgr,-targetPsgr.psgrNum)
                    self.globalVar.setEndPsgr(targetPsgr.psgrID)
                    targetPsgr.setTime("ARRIVAL", self.getTime())
                    arrivaltime = self.getTime()
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'arrivaltime' : arrivaltime})
                    else:
                        pass
                    targetPsgr.setState("END")
                    self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} drop off {} #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.psgrNum,targetShuttleID, targetPsgr.strArrivalNode))
                    timenow = self.getTime()
                    increased_time = (timenow - targetPsgr.departureTime) - targetPsgr.expectedArrivalTime
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'increased_time' : increased_time})
                    else:
                        pass
                    if targetPsgr.lastPsgr:
                        self.endPsgr = targetPsgr.psgrID
                    if self.endPsgr == self.globalVar.getCountEndPsgr():
                        self.simDone = True
            else :
                targetPsgr = self.globalVar.getPsgrInfoByID(transitInfo)
                self.globalVar.setFailPsgr(targetPsgr.psgrID)
                targetPsgr.setState("FAIL")
                self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} failed boarding".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.psgrNum))
                dep_node = targetPsgr.strDepartureNode
                if dep_node.startswith('dynamic_'):
                    self.globalVar.remove_dynamic_node(dep_node)
                if targetPsgr.shuttle_Fail == True:
                    success = "Shuttle_Fail"
                else:
                    success = "Passenger_Fail"
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'success' : False})
                else:
                    pass
                if targetPsgr.lastPsgr:
                    self.endPsgr = targetPsgr.psgrID
                if self.endPsgr == self.globalVar.getCountEndPsgr():
                    self.simDone = True
            self.transitlst.pop(0)
            return True
        elif self.state == "ANALYSIS":
            self.addOutputEvent("SimumlationComplete", True)
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        # CALL 상태에서 
        # 호출하는 승객이 없는 경우 wait 상태로 변환 
        # 호출하는 승객이 있는 경우 call 상태 유지 
        if self.state == "CALL":
            if len(self.passengerlst) == 0:
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[1]
            return True
        elif self.state == "TRANSIT":
            if self.simDone :
                self.state = self.stateList[3]
            elif len(self.transitlst) == 0:
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[2]
            return True
        elif self.state == "ANALYSIS":
            self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "CALL":
            return 0
        elif self.state == "TRANSIT":
            return 0
        elif self.state == "ANALYSIS":
            return 0
        else:
            return 999999999999
