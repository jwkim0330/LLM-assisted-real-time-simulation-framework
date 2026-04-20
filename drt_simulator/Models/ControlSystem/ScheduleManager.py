import random

from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel


INF = float('inf')


class ScheduleManager(DEVSAtomicModel):
    
    def __init__(self, strID, globalVar):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar

        # states
        self.stateList = ["IDLE", "DSPPP" ,"SCHEDULE"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("Call")
        self.addInputPort("DispatchRoute_Res")

        # output Ports
        self.addOutputPort("DispatchRoute_Req")
        self.addOutputPort("Schedule")
        self.addOutputPort("Transit")

        # self variables
        self.addStateVariable("strID", strID)
        
        # variables
        self.DSPlst = []
        self.schedulelst = []

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "Call":
            targetPsgr = self.globalVar.getPsgrInfoByID(objEvent)
            self.globalVar.printTerminal("[{}][{}] Call recevied Psgr #{} #{} to #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.strDepartureNode,targetPsgr.strArrivalNode))
            self.DSPlst.append(targetPsgr)
            if self.state == "IDLE":
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
                
        elif strPort == "DispatchRoute_Res":
            schedule = objEvent
            self.schedulelst.append(schedule)
            if str(type(schedule)) != "<class 'int'>" :
                self.globalVar.printTerminal("[{}][{}] SCHEDULE{} of {} recevied".format(self.getTime(), self.getStateValue("strID"), schedule.scheduleID ,schedule.shuttleID))
            if self.state == "IDLE":
                self.state = self.stateList[2]
            else:
                self.continueTimeAdvance()
            return True

    def funcOutput(self):
        if self.state == "DSPPP":
            targetPsgr = self.DSPlst[0]
            self.addOutputEvent("DispatchRoute_Req", targetPsgr)
            self.globalVar.printTerminal("[{}][{}] Dispatching sent Psgr #{} #{} to #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.strDepartureNode,targetPsgr.strArrivalNode))
            self.DSPlst.pop(0)
            return True
        elif self.state == "SCHEDULE":
            targetSchedule = self.schedulelst[0]
            if str(type(targetSchedule)) != "<class 'int'>" :
                self.addOutputEvent("Schedule", targetSchedule)
                self.globalVar.printTerminal("[{}][{}] SCHEDULE{} sent to {}".format(self.getTime(), self.getStateValue("strID"), targetSchedule.scheduleID, targetSchedule.shuttleID))
            else :
                targetPsgr = self.globalVar.getPsgrInfoByID(targetSchedule)
                self.addOutputEvent("Transit", targetPsgr.psgrID)
                self.globalVar.printTerminal("[{}][{}] Passenger #{} fail to scheduling".format(self.getTime(), self.getStateValue("strID"),targetSchedule ))
            self.schedulelst.pop(0)
            return True
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "IDLE":
            if len(self.DSPlst) == 0 :
                self.state = self.stateList[0]
            else :
                self.state = self.stateList[1]
            return True
        elif self.state == "DSPPP":
            self.state = self.stateList[0]
            return True
        elif self.state == "SCHEDULE":
            if len(self.schedulelst) == 0 :
                self.state = self.stateList[0]
            else :
                self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "IDLE":
            return 999999999999
        else:
            return 0
