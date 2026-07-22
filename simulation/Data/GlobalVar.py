import copy
import json
from collections import deque
import networkx as nx
import pickle


MAX_EDGE_VALUE = 99999999

class GlobalVar:
    def __init__(self, isTerminalOn, graph_data, node_data, ShuttleInfo, validGridList, validGridWeight, stopInfo,  jsonPath, numShuttle, scenarioID, isDBsave):

        self.networkInfo = nx.Graph()
        self.graphInfo = {}
        self.nodeInfo = {}
        
        self.psgrWaitingQueue = {}
        self.psgrRidingQueue = {}
        self.psgrArrivalQueue = {}
        self.psgrFailQueue = {}
        
        self.shuttleInfo = {}
        self.targetJobs = {}
        self.isTerminalOn = isTerminalOn
        self.jsonPath = jsonPath
        self.genInfo = {}

        self.setNodeInfo(node_data)
        self.setGraphInfo(graph_data)
        self.setNetworkInfo(graph_data)
        self.setGeneratorInfo(validGridList, validGridWeight, stopInfo)
        self.setShuttleInfo(ShuttleInfo, numShuttle)
        self.scenarioID = scenarioID
        self.isDBsave = isDBsave
        self.dynamic_node_counter = 1
        self.dynamic_node_mapping = {}

    ## function for Shuttle information ##
    def setShuttleInfo(self, Info, numShuttle):
        for i in range(numShuttle):
            self.shuttleInfo[Info[i]["shuttleID"]] = Shuttle(Info[i]["shuttleID"], Info[i]["node"])
            coordinates = self.getCoordinatesByNodeID(Info[i]["node"])
            if coordinates == None:
                print("Shuttle initiated at the wrong node")
            else:
                self.shuttleInfo[Info[i]["shuttleID"]].setCoordinates(coordinates)
        
    def getShuttleInfo(self):
        return self.shuttleInfo
    def getInitShuttleInfo(self):
        return self.initShuttleInfo
    def getShuttleInfoByID(self, ID):
        return self.shuttleInfo[str(ID)]   
    
    ## function for PSGR information ##   
    def setTargetPsgr(self, psgrID, psgrNum, DNode, ANode, psgrEDS, time,is_auto_generated):
        self.psgrWaitingQueue[psgrID] = Passenger(psgrID, psgrNum, DNode, ANode, psgrEDS, time,is_auto_generated)
    def getPsgrInfoByID(self, psgrID):
        psgr = None
        ## psgrWaitingQueue 는 generator에서 만들어진 객체가 대기하는 위치이다. 
        if psgrID in self.psgrWaitingQueue:
            psgr = self.psgrWaitingQueue[psgrID]
        elif psgrID in self.psgrRidingQueue:
            psgr = self.psgrRidingQueue[psgrID]
        elif psgrID in self.psgrArrivalQueue:
            psgr = self.psgrArrivalQueue[psgrID]
        elif psgrID in self.psgrFailQueue:
            psgr = self.psgrFailQueue[psgrID]
        else:
            print("psgrID is not existe")
        return psgr
    def setRidePsgr(self, psgrID):
        self.psgrRidingQueue[psgrID] = self.psgrWaitingQueue[psgrID]
        del self.psgrWaitingQueue[psgrID]
    def setEndPsgr(self, psgrID):
        self.psgrArrivalQueue[psgrID] = self.psgrRidingQueue[psgrID]
        del self.psgrRidingQueue[psgrID]
    def setFailPsgr(self, psgrID):
        self.psgrFailQueue[psgrID] = self.psgrWaitingQueue[psgrID]
        del self.psgrWaitingQueue[psgrID]
    def getCountEndPsgr(self):
        return len(self.psgrArrivalQueue) + len(self.psgrFailQueue) 
    def getEndPsgr(self):
        return self.psgrArrivalQueue , self.psgrFailQueue
    def getpsgrArrivalQueue(self):
        return self.psgrArrivalQueue
    def getpsgrFailQueue(self):
        return self.psgrFailQueue
    
    
    ## function for Generator information ##
    def setGeneratorInfo(self, validGridList, validGridWeight, stopInfo):
        self.genInfo["validGridList"] = validGridList
        self.genInfo["validGridWeight"] = validGridWeight
        self.genInfo["stopInfo"] = stopInfo
    def getGeneratorInfo(self):
        return self.genInfo
        
    ## function for node information ##
    def setNetworkInfo(self, Info):
        for node, data in Info.items():
            for neighbor, link_info in data['links'].items():
                self.networkInfo.add_edge(node, neighbor, time=link_info['time'], length=link_info['length'], max_spd=link_info['max_spd'], vector = link_info['vector'])
    
    def setGraphInfo(self, Info):
        self.graphInfo = Info
        
    def setNodeInfo(self, Info):
        self.nodeInfo = Info
    def getNodeInfo(self):
        return self.nodeInfo
    def getNodeInfoByID(self, ID):
        return self.nodeInfo[str(ID)]
    def getNearestNode(self, node_id, num_neighbors):
        visited = set()
        to_visit = deque([node_id])

        nearest_neighbors = []

        while to_visit and len(nearest_neighbors) < num_neighbors:
            current_node = to_visit.popleft()
            visited.add(current_node)

            neighbors = self.graphInfo[current_node]['neighbors']
            for neighbor in neighbors:
                link_info = self.graphInfo[current_node]['links'][neighbor]
                if neighbor not in visited:
                    nearest_neighbors.append(neighbor)
                    to_visit.append(neighbor)
                    visited.add(neighbor)
                if len(nearest_neighbors) == num_neighbors:
                    break
        return nearest_neighbors[:num_neighbors]


    ## function for nodeID returns ##
    def getNodeIDByCoordinates(self, coordinates):
        for key, value in self.nodeInfo.items():
            if value.lstCoordinates == coordinates:
                return key
        print("Function getNodeIDByCoordinates() Error")
        return None
    
    ## function for coordinate returns ##
    def getCoordinatesByNodeID(self, nodeID):
        for key, value in self.nodeInfo.items():
            if key == nodeID:
                return value
        print("Function getCoordinatesByNodeID() Error")
        return None

    ## function for nextNodeID retrieval
    def getNextNodeIDByNodeID(self, nodeID):
        searchID = str(nodeID)
        if searchID in self.nextNodeInfo:
            return self.nextNodeInfo[searchID]
        else:
            print("next node doesn't exist!!")
  
    ## funtion for print ##
    def printTerminal(self, log):
        if self.isTerminalOn == True:
            print(log)

    def find_nearest_nodes(self, x, y, num_neighbors=1):
        distances = []
        for node_id, coordinates  in self.nodeInfo.items():
            if node_id.startswith('dynamic_'):
                continue  # 동적 노드면 건너뜁니다.
            node_x, node_y = coordinates 
            distance = ((x - node_x) ** 2 + (y - node_y) ** 2) ** 0.5
            distances.append((distance, node_id))
        distances.sort()
        nearest_nodes = [node_id for _, node_id in distances[:num_neighbors]]
        return nearest_nodes

    def add_dynamic_node(self, x, y, num_neighbors=1):
        new_node_id = f'dynamic_{self.dynamic_node_counter}'
        self.dynamic_node_counter += 1

        # 가장 가까운 노드들을 먼저 찾습니다.
        nearest_nodes = self.find_nearest_nodes(x, y, num_neighbors)
        nearest_node_id = nearest_nodes[0]
        nearest_node_coords = self.nodeInfo[nearest_node_id]
        neighbor_x, neighbor_y = nearest_node_coords

        # 새로운 노드를 nodeInfo에 추가
        self.nodeInfo[new_node_id] = (x, y)

        # 그래프 정보에 추가
        self.graphInfo[new_node_id] = {
            'coordinates': (x, y),
            'neighbors': set(),  # 집합으로 초기화
            'links': {}
        }

        # 동적 노드와 가장 가까운 노드의 연결 정보 저장
        distance = ((x - neighbor_x) ** 2 + (y - neighbor_y) ** 2) ** 0.5
        speed = 30  # 필요에 따라 속도 설정
        time = distance / speed

        # 동적 노드 매핑에 저장
        self.dynamic_node_mapping[new_node_id] = {
            'nearest_node_id': nearest_node_id,
            'link_time': time
        }

        # 그래프 정보에 연결 추가
        self.graphInfo[new_node_id]['links'][nearest_node_id] = {
            'length': distance,
            'time': time,
            'max_spd': speed,
            'vector': {'x': neighbor_x - x, 'y': neighbor_y - y}  # 딕셔너리 형태로 저장
        }

        # 반대 방향 링크 추가
        self.graphInfo[nearest_node_id]['neighbors'].add(new_node_id)
        self.graphInfo[nearest_node_id]['links'][new_node_id] = {
            'length': distance,
            'time': time,
            'max_spd': speed,
            'vector': {'x': x - neighbor_x, 'y': y - neighbor_y}
        }

        # 네트워크 그래프에 엣지 추가
        self.networkInfo.add_edge(new_node_id, nearest_node_id, time=time, length=distance,
                                max_spd=speed, vector={'x': neighbor_x - x, 'y': neighbor_y - y})

        self.networkInfo.add_edge(nearest_node_id, new_node_id, time=time, length=distance,
                        max_spd=speed, vector={'x': x - neighbor_x, 'y': y - neighbor_y})
        
        return new_node_id
    
    def remove_dynamic_node(self, node_id):
        # 그래프에서 노드 제거
        if node_id in self.graphInfo:
            # 연결된 노드들의 정보 업데이트
            for neighbor_id in self.graphInfo[node_id]['neighbors']:
                self.graphInfo[neighbor_id]['neighbors'].remove(node_id)
                del self.graphInfo[neighbor_id]['links'][node_id]
                # 네트워크 그래프에서 엣지 제거
                if self.networkInfo.has_edge(node_id, neighbor_id):
                    self.networkInfo.remove_edge(node_id, neighbor_id)
            # 그래프 정보에서 노드 제거
            del self.graphInfo[node_id]
        # 노드 정보에서 노드 제거
        if node_id in self.nodeInfo:
            del self.nodeInfo[node_id]
        # 네트워크 그래프에서 노드 제거
        if self.networkInfo.has_node(node_id):
            self.networkInfo.remove_node(node_id)

class Node:
    def __init__(self, nodeID, coordinates, isSubNode):
        self.strNodeID = str(nodeID)
        self.lstCoordinates = coordinates
        self.isEquipment = False
        self.isReserved = False
        self.usageCnt = 0
        self.isSubNode = isSubNode
        self.isBranch = False
        self.isConfluence = False
        # for dijkstra
        self.dist = MAX_EDGE_VALUE
        self.post = 0

class Shuttle:
    def __init__(self, shuttleID, node):
        self.strShuttleID = str(shuttleID)
        self.coordinates = None
        self.strState = "IDLE"                      # IDLE, MOVE, BOARD
        self.dictActivationTime = {}
        self.dictPsgrLoad = {}
        self.curNode = node
        self.doneWaitStartTime = None
        self.maxPsgr = 9
        self.curPsgrNum = 0
        self.curPsgr = []
        self.curPath = []
        self.curDst = []
        self.schedule = None
        
    def setState(self, state):
        self.strState = state

    def setCoordinates(self, coorinates):
        self.coordinates = coorinates
    
    def adjustPsgr(self, psgr, psgrNum):
        self.curPsgrNum = self.curPsgrNum + psgrNum
        if psgrNum > 0:
            self.curPsgr.append(psgr)
        else :
            self.curPsgr.remove(psgr)
        
    def setPath(self, path):
        self.curPath = path
    
    def setDstLst(self, dstLst) :
        self.curDst = dstLst
        
    def delDst(self):
        self.curDst.pop(0)
        
    def setNode(self, node):
        self.curNode = node

    def getcurPsgr(self):
        return self.curPsgr
    
    def setSchedule(self, schedule):
        self.schedule = schedule
        
    def setActivationTime(self, psgrID, time):
        if psgrID not in self.dictActivationTime:
            self.dictActivationTime[psgrID] = time
        else:
            self.dictActivationTime[psgrID] = self.dictActivationTime[psgrID] + time
            
    def setPsgrLoad(self, psgrCnt, time):
        if psgrCnt not in self.dictPsgrLoad:
            self.dictPsgrLoad[psgrCnt] = time
        else:
            self.dictPsgrLoad[psgrCnt] = self.dictPsgrLoad[psgrCnt] + time
#Generator.py의 funcoutput에서 다음과 같은 방식으로 호출이 된다. : self.globalVar.setTargetPsgr(self.psgrID, psgrNum, dep_node, arr_node, psgrEDS, self.getTime())
class Passenger:
    # psgrID: 제너레이터에서 사용자마다 1씩 증가시키는 방식으로 선정,승객 그룹의 아이디
    # psgrNum: 승객 그룹의 승객 수 
    # DNode : 승객 그룹이 출발하는 위치
    # ANode : 승객 그룹이 도착하는 위치 
    # psgrEDS : 우선 처리 요소를 적용할것인지의 불린값, 우리는 false로 사용
    # time : 승객이 호출하는 현재 시간 
    def __init__(self, psgrID, psgrNum, DNode, ANode, psgrEDS, time,is_auto_generated):
        self.psgrID = int(psgrID)
        self.strState = "WAIT"
        self.waitingStartTime = time
        self.departureTime = 0
        self.arrivalTime = 0
        self.strShuttleID = ""
        self.strArrivalNode = ANode
        self.strDepartureNode = DNode
        self.psgrNum = psgrNum
        self.expectedWatingTime = 0
        self.expectedArrivalTime = 0 # 탑승시간
        self.lastPsgr = False
        self.psgrEDS = psgrEDS
        self.bestpath = []
        self.pathChanged = 0
        self.increasedTime = 0
        self.shuttle_Fail = False
        self.is_auto_generated=is_auto_generated
    # 마지막 탑승자는 lastPsgr=True로 하고 이게 다른 요소의 트리거가 되어 작업이 종료되나봄    
    def setlastPsgr(self):
        self.lastPsgr = True
        
    def plusPath(self):
        self.pathChanged += 1  
        
    def setExpectedTime(self, expectedWatingTime, expectedArrivalTime):
        self.expectedWatingTime = expectedWatingTime
        self.expectedArrivalTime = expectedArrivalTime
    #승객은 wait boarding end 3가지의 상태만을 가질 수 있다. 
    def setState(self, state):
        if state == "WAIT" or "BOARDING" or "END":
            self.strState = state
        else:
            print("Wrong input 'state'")
    # 상태에 따라서 현재 시간을 그에 맞게 정한다. setTime은 상태 천이가 일어난 후 바로 작동시켜서 시간이 지나가기 전에 특정 상태를 저장해주는 역할을 할 것 같다. 
    def setTime(self, state, time):
        if state == "WAIT":
            self.waitingStartTime = time
        elif state == "DEPARTURE":
            self.departureTime = time
        elif state == "ARRIVAL":
            self.arrivalTime = time
        else:
            print("Wrong input 'state'")
    # 셔틑을 배정하는 메서드 
    def setPsgrShuttle(self, shuttleID):
        self.strShuttleID = shuttleID
    # 어떤 사건이 발생하면 시간이 증가한다. 여기서 어떤 사건이 무엇이 될지는 더 살펴보아야한다. 
    def setIncreasedTime(self, increasedTime):
        self.increasedTime = increasedTime
