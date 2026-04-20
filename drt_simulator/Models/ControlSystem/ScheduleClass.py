class Schedule:
        def __init__(self, psgrID, shuttleID, strDepartureNode, strArrivalNode, dstLst ,totalPath, totalPathTime, newPsgrWaitTime, newPsgrArrivalTime, total_increased_boarding_time, total_increased_waiting_time):
            self.shuttleID = shuttleID
            self.psgrID = psgrID
            self.strDepartureNode = strDepartureNode
            self.strArrivalNode = strArrivalNode
            self.dstLst = dstLst
            self.totalPath = totalPath
            self.totalPathTime = totalPathTime
            self.newPsgrWaitTime = newPsgrWaitTime
            self.newPsgrArrivalTime = newPsgrArrivalTime
            self.scheduleID = -1
            self.increased_boarding_time = total_increased_boarding_time
            self.increased_waiting_time = total_increased_waiting_time 