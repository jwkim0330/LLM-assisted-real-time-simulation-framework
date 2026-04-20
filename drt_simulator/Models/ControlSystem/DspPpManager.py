import random
import itertools
from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from Models.ControlSystem.ScheduleClass import Schedule
import networkx as nx
from collections import defaultdict
from scipy.spatial.distance import directed_hausdorff
from dtaidistance import dtw
import matplotlib.pyplot as plt
import os
import pickle
from datetime import datetime
import numpy as np
from frechetdist import frdist
import math
from DataServer import KPIDataSaver

INF = float('inf')


class DspPpManager(DEVSAtomicModel):

    def __init__(self, strID, globalVar):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()

        # states
        self.stateList = ["IDLE", "SCHEDULE"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("DispatchRoute_Req")

        # output Ports
        self.addOutputPort("DispatchRoute_Res")
        self.addOutputPort("Result_Notification")
        

        # self variables
        self.addStateVariable("strID", strID)

        # variables
        self.DSPlst = []
        self.scheduleID = 0
        filename = 'shortest_paths.pkl'
        filepath = os.path.join(os.path.dirname(__file__), filename)
        self.shortest_paths = self.load_shortest_paths(filepath)
        self.x_min = 475
        self.x_max = 1467
        self.y_min = 1488
        self.y_max = 2271


    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "DispatchRoute_Req":
            targetPsgr = objEvent
            self.globalVar.printTerminal("[{}][{}] Dispatching recevied Psgr #{} #{} to #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.strDepartureNode,targetPsgr.strArrivalNode))
            self.DSPlst.append(targetPsgr)
            if self.state == "IDLE":
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True

    def funcOutput(self):
        if self.state == "SCHEDULE":
            networkInfo = self.globalVar.networkInfo
            targetPsgr = self.DSPlst[0]
            targetShuttledic = self.dispatching(targetPsgr.psgrNum)

            shuttles_with_path = {shuttle_id: shuttle for shuttle_id, shuttle in targetShuttledic.items() if shuttle.curPath}
            shuttles_without_path = {shuttle_id: shuttle for shuttle_id, shuttle in targetShuttledic.items() if not shuttle.curPath}

            for shuttle_id, shuttle in targetShuttledic.items(): 
                if not shuttle.curPath:
                    self.globalVar.printTerminal(shuttle.curPath)

            if len(targetShuttledic) == 0:
                self.globalVar.printTerminal("[{}][{}] Every Shuttle is full".format(self.getTime(), self.getStateValue("strID")))
                self.addOutputEvent("DispatchRoute_Res", targetPsgr.psgrID)
                self.DSPlst.pop(0)
                return True
            else:
                # 경로가 있는 애들은 3개를 선정하고, 없는 애들은 그 이후 따로 추가 더 고도화하면 경로가 없는 애들은 시작점이 600이하인지 체크
                if shuttles_with_path:
                    similar_shuttles = self.find_similar_shuttles(targetPsgr, targetShuttledic, self.shortest_paths, networkInfo)
                    targetShuttledic = {shuttle_id: shuttles_with_path[shuttle_id] for shuttle_id in similar_shuttles}
                for shuttle_id, shuttle in shuttles_without_path.items():
                    targetShuttledic[shuttle_id] = shuttle

                scheduledic = {}
                satisfaction_data =[]
                Suttle_fail_check = True
                min_new_call_time = float('inf')
                min_boarding_increase_time = float('inf')
                min_waiting_increase_time = float('inf')

                for key, shuttle in targetShuttledic.items():
                    tempSchedule = self.pathPlanning(shuttle, targetPsgr)
                    if tempSchedule is None:
                        continue

                    new_call_total_time = tempSchedule.newPsgrWaitTime + tempSchedule.newPsgrArrivalTime

                    min_new_call_time = min(min_new_call_time, new_call_total_time)
                    min_boarding_increase_time = min(min_boarding_increase_time, tempSchedule.increased_boarding_time)
                    min_waiting_increase_time = min(min_waiting_increase_time, tempSchedule.increased_waiting_time)

                    scheduledic[key] = tempSchedule
                    satisfaction_data.append({
                        "shuttle_id": key,
                        "new_call_time": new_call_total_time,
                        "increased_boarding_time": tempSchedule.increased_boarding_time,
                        "increased_waiting_time": tempSchedule.increased_waiting_time
                    })

                bestShuttleID = None
                maxTotalSatisfaction = -float('inf')

                self.globalVar.printTerminal(satisfaction_data)
                for data in satisfaction_data:
                    shuttle_id = data["shuttle_id"]
                    new_call_satisfaction = self.calculate_satisfaction_with_exponential_decay(
                        actual_time=data["new_call_time"],
                        min_time=min_new_call_time,
                        decay_rate=0.001  # 적절한 decay_rate 설정
                    )

                    boarding_satisfaction = self.calculate_satisfaction_with_exponential_decay(
                        actual_time=data["increased_boarding_time"],
                        min_time=min_boarding_increase_time,
                        decay_rate=0.001
                    )

                    waiting_satisfaction = self.calculate_satisfaction_with_exponential_decay(
                        actual_time=data["increased_waiting_time"],
                        min_time=min_waiting_increase_time,
                        decay_rate=0.001
                    )
                    
                    # 두 만족도를 가중치에 따라 합산하여 최종 만족도 계산
                    total_satisfaction = self.calculate_total_satisfaction(
                        new_call_satisfaction,
                        boarding_satisfaction,
                        waiting_satisfaction,
                        w_new_call=0.4,  # 새로운 콜에 대한 가중치
                        w_boarding=0.3,
                        w_waiting=0.3   # 기존 승객에 대한 가중치
                    )

                    # 가장 높은 만족도를 가진 차량 선택,하한값 존재,  
                    self.globalVar.printTerminal(scheduledic[shuttle_id].newPsgrWaitTime)
                    if total_satisfaction > maxTotalSatisfaction and scheduledic[shuttle_id].newPsgrWaitTime < 900:
                        maxTotalSatisfaction = total_satisfaction
                        bestShuttleID = shuttle_id
                        Suttle_fail_check = False

                if bestShuttleID is not None  :
                    self.addOutputEvent("DispatchRoute_Res", scheduledic[bestShuttleID])
                    ## 배차에 성공한 경우 성공 메시지 전달 및 배차 차량 id 전달(bestShittleID)
                    
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'shuttleid': bestShuttleID}) ##예측되는 배차 차량을 먼저 저장해서 가시화에 용이하게 설정  
                    
                    if targetPsgr.is_auto_generated==False:    
                        Result={"is_assigned_shuttle":True,"shuttle_id":bestShuttleID,"passenger_ID":targetPsgr.psgrID}
                        self.addOutputEvent("Result_Notification",Result) 
                    self.scheduleID = self.scheduleID+1
                    scheduledic[bestShuttleID].scheduleID = '{:03}'.format(self.scheduleID)
                    self.globalVar.printTerminal("[{}][{}] {} start #{} to #{}".format(self.getTime(), self.getStateValue("strID"),  bestShuttleID, targetShuttledic[bestShuttleID].curNode, scheduledic[bestShuttleID].strDepartureNode))
                else :
                    if Suttle_fail_check == True:
                        targetPsgr.shuttle_Fail = True
                    self.addOutputEvent("DispatchRoute_Res", targetPsgr.psgrID)
                    ## 배차에 실패한 경우 실패 메시지 전달 
                    if targetPsgr.is_auto_generated==False:    
                        Result={"is_assigned_shuttle":False}
                        self.addOutputEvent("Result_Notification",Result)
                    self.globalVar.printTerminal("[{}][{}] Dispatching of Passenger #{} failed".format(self.getTime(), self.getStateValue("strID"),  targetPsgr.psgrID))
                
                self.DSPlst.pop(0)
            return True
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "SCHEDULE":
            if len(self.DSPlst) == 0 :
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "SCHEDULE":
            return 0
        else:
            return 999999999999
        
    def dispatching(self, psgrNum):
        targetShuttledic = {}
        shuttleInfo = self.globalVar.getShuttleInfo()
        for key, value in shuttleInfo.items():
            if value.curPsgrNum + psgrNum <= value.maxPsgr:
                targetShuttledic[key] = value
        return targetShuttledic
    

    def pathPlanning(self, shuttle, targetPsgr):
        curDst = shuttle.curDst
        curNodeID = shuttle.curNode
        curPsgrNum = shuttle.curPsgrNum
        shuttle = shuttle
        
        targetDeparture = targetPsgr.strDepartureNode
        targetArrival = targetPsgr.strArrivalNode
        networkInfo = self.globalVar.networkInfo

        totalPath = []
        psgrID = targetPsgr.psgrID
        totalPathTime = 0
        newPsgrWaitTime = 0
        newPsgrArrivalTime = 0
        total_increased_boarding_time = 0
        total_increased_waiting_time = 0
        dstLst = []

        if len(curDst) == 0:
            shuttleToDepPath, newPsgrWaitTime = self.find_shortest_path(networkInfo, curNodeID, targetDeparture)
            depToArvPath, depToArvPathTime = self.find_shortest_path(networkInfo, targetDeparture, targetArrival)
            dstLst = []
            dstLst.append((targetDeparture, "BOARDING", targetPsgr.psgrID, targetPsgr.psgrEDS, +targetPsgr.psgrNum))
            dstLst.append((targetArrival, "DROPPING", targetPsgr.psgrID, targetPsgr.psgrEDS, -targetPsgr.psgrNum))
            
            totalPath = shuttleToDepPath[:-1] + depToArvPath
            totalPathTime = newPsgrWaitTime + depToArvPathTime
            newPsgrArrivalTime = depToArvPathTime
        else:
            nodeList, EDList, psgrCountCheck = [], [], []
            for event in curDst:
                nodeList.append(event[0])
                EDList.append(event[3])
                psgrCountCheck.append(event[4])

            best_point, best_total_time, total_increased_boarding_time, total_increased_waiting_time = \
                self.find_optimal_insertion(nodeList, EDList, psgrCountCheck, targetDeparture, targetArrival, networkInfo, targetPsgr, curPsgrNum, shuttle)

            if best_point is None:
                return None

            dstLst = curDst.copy()
    
            boarding_index = best_point.index('9998')
            dropping_index = best_point.index('9999')
            
            boarding_event = (targetDeparture, "BOARDING", targetPsgr.psgrID, targetPsgr.psgrEDS, +targetPsgr.psgrNum)
            dstLst.insert(boarding_index, boarding_event)
            
            dropping_event = (targetArrival, "DROPPING", targetPsgr.psgrID, targetPsgr.psgrEDS, -targetPsgr.psgrNum)
            dstLst.insert(dropping_index, dropping_event)
            
            totalPath, totalPathTime, newPsgrWaitTime, newPsgrArrivalTime = self.find_final_path(networkInfo, curNodeID, [event[0] for event in dstLst], targetDeparture, targetArrival)
            # 새로운 콜에 비중을 둘지, 타고 있는 손님에 비중을 둘지 결정
        
        schedule = Schedule(psgrID, shuttle.strShuttleID, targetDeparture, targetArrival, dstLst, totalPath, totalPathTime, newPsgrWaitTime, newPsgrArrivalTime, total_increased_boarding_time, total_increased_waiting_time)

        return schedule
    
    
    
    def find_shortest_path(self, networkInfo, start_node, end_node):        
        try:
            path = nx.shortest_path(networkInfo, source=start_node, target=end_node, weight='time')
            path_length = nx.shortest_path_length(networkInfo, source=start_node, target=end_node, weight='time')
            return path, path_length
        except nx.NetworkXNoPath:
            return None, float('inf')  # Return infinity if no path exists


    def find_final_path(self, networkInfo, curNodeID, best_path, targetDeparture, targetArrival):
        final_path = []
        total_time = 0
        newPsgrWaitTime = 0
        newPsgrArrivalTime = 0
        departureFound = False
        arrivalFound = False

        for i, node in enumerate(best_path):
            if i == 0:
                segment_path, segment_time = self.find_shortest_path(networkInfo, curNodeID, node)
            else:
                segment_path, segment_time = self.find_shortest_path(networkInfo, best_path[i-1], node)
            
            if not departureFound:
                newPsgrWaitTime += segment_time
                if node == targetDeparture:
                    departureFound = True
            elif not arrivalFound:
                newPsgrArrivalTime += segment_time
                if node == targetArrival:
                    arrivalFound = True

            total_time += segment_time
            
            if i > 0:
                final_path.extend(segment_path[1:])
            else:
                final_path.extend(segment_path)

        return final_path, total_time, newPsgrWaitTime, newPsgrArrivalTime
    

    def find_optimal_insertion(self, existing_destinations, EDList, psgrCountCheck,targetDeparture, targetArrival, networkInfo, targetPsgr, curPsgrNum, shuttle):
        best_path = None
        best_total_time = float('inf')
        check_waiting_time = True
        check_baording_time = True
        total_increased_waiting_time = 0
        total_increased_boarding_time = 0
        insertable_positions = []

        if not EDList[0]:
            insertable_positions.append((0,0))

        for i in range(1, len(EDList)):
            if not EDList[i-1] and EDList[i]:
                insertable_positions.append((i, i))
            elif not EDList[i]:
                insertable_positions.append((i, i+1))
                
        insertable_positions.append((len(existing_destinations), len(existing_destinations)))

        if targetPsgr.psgrEDS:
            for i, j in insertable_positions:
                temp_path = existing_destinations[:i] + [targetDeparture] + [targetArrival] + existing_destinations[i:]
                count_path = psgrCountCheck[:i] + [+targetPsgr.psgrNum] + [-targetPsgr.psgrNum] + psgrCountCheck[i:]
                possible_count = curPsgrNum
                over_capacity = False
                
                for k in range(len(count_path)):
                    possible_count += count_path[k]
                    if possible_count > 9:
                        over_capacity = True
                        break
                    
                if over_capacity == True:
                    continue
                
                try:
                    total_time = self.calculate_total_time(temp_path, networkInfo)
                    if total_time < best_total_time:
                        best_total_time = total_time
                        best_path = existing_destinations[:i] + ['9998'] + ['9999'] + existing_destinations[i:]
                except nx.NetworkXNoPath:
                    continue
        else : 
            for i, j in insertable_positions:
                temp_path = existing_destinations[:i] + [targetDeparture] + existing_destinations[i:j] + [targetArrival] + existing_destinations[j:]
                count_path = psgrCountCheck[:i] + [+targetPsgr.psgrNum] + psgrCountCheck[i:j] + [-targetPsgr.psgrNum] + psgrCountCheck[j:]
                possible_count = curPsgrNum 
                over_capacity = False
                
                for k in range(len(count_path)):
                    possible_count += count_path[k]
                    if possible_count > 9:
                        over_capacity = True
                        break
                
                if over_capacity == True:
                    continue
                
                try:
                    total_time = self.calculate_total_time(temp_path, networkInfo)
                    
                    check_waiting_time, total_increased_waiting_time = self.calculate_waiting_time(temp_path, shuttle, networkInfo)

                    if len(shuttle.curPsgr) != 0:
                        temp_incresed_time, total_increased_boarding_time = self.calculate_increasing_boarding_time(temp_path, shuttle, networkInfo)
                        for curPsgr in shuttle.curPsgr:
                            if temp_incresed_time[curPsgr.psgrID] > 600:
                                check_baording_time = False
                                break
                    
                    # 최적 경로 선택 조건: 시간 증가와 대기 시간 증가가 모두 기준 이하인 경우 선택
                    if check_waiting_time == True and check_baording_time == True:
                        if total_time < best_total_time:
                            best_total_time = total_time 
                            best_path = existing_destinations[:i] + ['9998'] + existing_destinations[i:j] + ['9999'] + existing_destinations[j:]

                except nx.NetworkXNoPath:
                    continue

        if best_path is None:
            return None, float('inf'), total_increased_boarding_time, total_increased_waiting_time
                
        return best_path, best_total_time , total_increased_boarding_time , total_increased_waiting_time


    def calculate_total_time(self, path, networkInfo):
        total_time = 0
        for i in range(len(path)-1):
            segment_time = nx.shortest_path_length(networkInfo, source=path[i], target=path[i+1], weight='time')
            total_time += segment_time
        return total_time
    
    def calculate_increasing_boarding_time (self, temp_path, shuttle, networkInfo):
        increased_times = {}
        total_increased_time = 0

        # curPath에서 curPsgr의 출발지와 도착지를 검색한 후 해당 거리 계산
        # tempPath에서 curPsgr의 출발지와 도착지를 검색한 후 해당 거리 계산 후 앞이랑 비교
        for curPsgr in shuttle.curPsgr:
            # 승객의 출발지와 도착지 노드 가져오기
            curNode = shuttle.curNode
            arrival_node = curPsgr.strArrivalNode
            timenow = self.getTime()
            boarding_time = timenow - curPsgr.departureTime
            
            # tempSchedule의 totalPath에서 새로운 경로 시간 계산
            newPath = temp_path

            if curNode not in newPath:
                segment_path, segment_time = self.find_shortest_path(networkInfo, curNode, newPath[0])
                # segment_path를 newPath의 앞에 붙입니다.
                newPath = segment_path[:-1] + newPath

            if curNode in newPath and arrival_node in newPath:
                new_subpath = newPath[newPath.index(curNode):newPath.index(arrival_node) + 1]
                new_time = self.calculate_total_time(new_subpath, networkInfo)
            else:
                new_time = None  # 승객의 노드가 새로운 경로에 없음

            
            # 경로 시간 증가량 계산 및 리스트에 추가
            if new_time is not None:
                increased_time = (new_time + boarding_time) - curPsgr.expectedArrivalTime
                increased_times[curPsgr.psgrID] = increased_time
                total_increased_time += increased_time
                new_time = None

        
        return increased_times, total_increased_time  
    

    def calculate_waiting_time(self, temp_path, shuttle, networkInfo):
        self.check_waiting_times = True
        waiting_times = {}
        total_increased_waiting_time = 0

        for curDst in shuttle.curDst:
            if curDst[1] == 'BOARDING':
                curPsgr = self.globalVar.getPsgrInfoByID(curDst[2])
                curNode = shuttle.curNode
                departure_node = curPsgr.strDepartureNode
                timenow = self.getTime()
                self.waiting_time = timenow - curPsgr.waitingStartTime
                self.new_waiting_time = None
                newPath = temp_path

                if curNode not in newPath:
                    segment_path, segment_time = self.find_shortest_path(networkInfo, curNode, newPath[0])
                    # segment_path를 newPath의 앞에 붙입니다.
                    newPath = segment_path[:-1] + newPath

                if departure_node in newPath:
                    new_subpath = newPath[newPath.index(curNode):newPath.index(departure_node) + 1]
                    self.new_waiting_time = self.calculate_total_time(new_subpath, networkInfo)
                else:
                    print("웨이팅 타임 계산 오류")

                if self.new_waiting_time is not None:
                    increased_waiting_time = self.new_waiting_time + self.waiting_time
                    waiting_times[curPsgr.psgrID] = increased_waiting_time
                    total_increased_waiting_time += increased_waiting_time

                    # 대기 시간이 600초 이상이면 만족도와 대기 시간 계산 중단
                    if increased_waiting_time > 600:
                        self.check_waiting_times = False
                        break
                    else:
                        pass
                

        return self.check_waiting_times, total_increased_waiting_time
    
    def calculate_satisfaction_with_exponential_decay(self, actual_time, min_time, decay_rate):
        if actual_time <= min_time:
            return 1.0
        else:
            return math.exp(-decay_rate * (actual_time - min_time))
        
    def calculate_total_satisfaction(self, new_call_satisfaction, boarding_passenger_satisfaction, waiting_passenger_satisfaction, w_new_call, w_boarding, w_waiting):
        total_satisfaction = (w_new_call * new_call_satisfaction) + (w_boarding * boarding_passenger_satisfaction) + (w_waiting*waiting_passenger_satisfaction)
        return total_satisfaction
        
    def find_similar_shuttles(self, targetPsgr, targetShuttledic, shortest_paths, networkInfo):
        # 타겟 승객 경로 계산
        shuttle_scores = []
        time_limit = 600 # 대기시간 변경해야함

        for shuttle_id, shuttle in targetShuttledic.items():
            closest_node, min_time = self.find_closest_node_with_precomputed_times(shuttle.curPath, targetPsgr.strDepartureNode, shortest_paths, time_limit)
            current_node = shuttle.curNode
            if targetPsgr.strDepartureNode.startswith('dynamic_'):
                dynamic_info = self.globalVar.dynamic_node_mapping[targetPsgr.strDepartureNode]
                nearest_node_id = dynamic_info['nearest_node_id']
                link_time = dynamic_info['link_time']
                precomputed_time = shortest_paths.get(current_node, {}).get(nearest_node_id)
                if precomputed_time is not None:
                    time_to_departure = precomputed_time + link_time
                else:
                    # 경로가 없으면 무한대로 설정
                    time_to_departure = float('inf')
            else:
                time_to_departure = shortest_paths.get(current_node, {}).get(targetPsgr.strDepartureNode, float('inf'))
                
            if closest_node and min_time < 600 and time_to_departure < time_limit:
                target_route, target_route_vector = self.calculate_target_route(targetPsgr, closest_node, networkInfo)
                shuttle_route_vector = self.calculate_route_vector(shuttle.curPath, networkInfo)
                
                if len(shuttle_route_vector) != 0:
                    similarity_score = self.calculate_frechet_distance(target_route_vector, shuttle_route_vector)
                    shuttle_scores.append((shuttle_id, similarity_score, target_route))  # target_route 추가
            
        # 유사도에 따라 정렬하고 상위 3개 선택
        shuttle_scores.sort(key=lambda x: x[1])
        top_shuttles = shuttle_scores[:3]

        # 상위 3개의 셔틀 ID로 targetShuttledic 필터링
        filtered_shuttles = {shuttle_id: targetShuttledic[shuttle_id] for shuttle_id, _, _ in top_shuttles}

        # 시각화 및 이미지 저장
        # shuttle_routes = [(filtered_shuttles[shuttle_id].curPath, target_route) for shuttle_id, _, target_route in top_shuttles]
        # self.visualize_and_save_routes(shuttle_routes, networkInfo)

        return filtered_shuttles

    def calculate_dtw_distance_with_vectors(self, route1, route2):

        if len(route1) > len(route2):
            route2.extend([{'x': 0, 'y': 0}] * (len(route1) - len(route2)))
        elif len(route2) > len(route1):
            route1.extend([{'x': 0, 'y': 0}] * (len(route2) - len(route1)))
        # 두 경로에 대해 벡터 거리 행렬 생성
        distance_matrix = np.zeros((len(route1), len(route2)))
        for i, vector1 in enumerate(route1):
            for j, vector2 in enumerate(route2):
                distance_matrix[i, j] = self.vector_distance(vector1, vector2)

        # 벡터 거리 행렬에 대해 DTW 계산
        dtw_distance = dtw.distance_matrix_fast(distance_matrix)
        total_dtw_distance = dtw_distance[-1, -1]

        return total_dtw_distance
    
    def vector_distance(self, v1, v2):
    # 튜플 형식의 벡터에서 각 요소를 가져와서 유클리드 거리를 계산
        return np.linalg.norm(np.array([v1['x'], v1['y']]) - np.array([v2['x'], v2['y']]))
    
    def calculate_frechet_distance(self, route1, route2):
        # 경로 길이를 동일하게 맞춤
        if len(route1) > len(route2):
            route2.extend([{'x': 0, 'y': 0}] * (len(route1) - len(route2)))
        elif len(route2) > len(route1):
            route1.extend([{'x': 0, 'y': 0}] * (len(route2) - len(route1)))
        route1_tuples = [(point['x'], point['y']) for point in route1]
        route2_tuples = [(point['x'], point['y']) for point in route2]

        try:
            distance = frdist(route1_tuples, route2_tuples)
        except Exception as e:
            print(f"Error in calculating Frechet distance: {e}")
            return float('inf')

        return distance

    def calculate_target_route(self, targetPsgr, closest_node, networkInfo):
        # 차량의 현재 위치에서 출발 노드, 도착 노드를 지나는 경로 계산
        route = []
        departureNodeID = targetPsgr.strDepartureNode
        arrivalNodeID = targetPsgr.strArrivalNode

        closest_to_departure_path, _ = self.find_shortest_path(networkInfo, closest_node, departureNodeID)
        if not closest_to_departure_path:
            print(f"Error: No path found from {closest_node} to {departureNodeID}")
        route.extend(closest_to_departure_path)

        departure_to_arrival_path, _ = self.find_shortest_path(networkInfo, departureNodeID, arrivalNodeID)
        if not departure_to_arrival_path:
            print(f"Error: No path found from {departureNodeID} to {arrivalNodeID}")
        route.extend(departure_to_arrival_path)
        
        return route, self.calculate_route_vector(route, networkInfo)

    def calculate_route_vector(self, route, networkInfo):
        vectors = []
        for i in range(len(route) - 1):
            source_node = route[i]
            target_node = route[i + 1]
            if source_node == target_node:
                continue    
            # source_node와 target_node를 사용해 링크의 벡터를 가져옴
            edge_data = networkInfo.get_edge_data(source_node, target_node)
            if edge_data and 'vector' in edge_data:
                vector = edge_data['vector']
                vectors.append(vector)

        if not vectors:
            print(f"Error: No vectors calculated for route: {route}")
            
        return vectors
    
    def find_closest_node_with_precomputed_times(self, vehicle_route, start_node, shortest_paths, time_limit):
        closest_node = None
        min_time = float('inf')

        for node in vehicle_route:
            if start_node.startswith('dynamic_'):
                dynamic_info = self.globalVar.dynamic_node_mapping[start_node]
                nearest_node_id = dynamic_info['nearest_node_id']
                link_time = dynamic_info['link_time']
                precomputed_time  = shortest_paths.get(node, {}).get(nearest_node_id)
                if precomputed_time  is not None:
                    time_to_start_node = precomputed_time  + link_time
                else:
                    time_to_start_node = float('inf')
            else:
                time_to_start_node = shortest_paths.get(node, {}).get(start_node, float('inf'))

            if time_to_start_node < min_time and time_to_start_node < time_limit:
                closest_node = node
                min_time = time_to_start_node
        
        return closest_node, min_time

    def visualize_and_save_routes(self, shuttle_and_target_routes, networkInfo, output_dir='route_visualizations'):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        colors = ['blue', 'green', 'yellow']

        for i, (shuttle_route, target_route) in enumerate(shuttle_and_target_routes):
            plt.figure(figsize=(10, 10))

            # 타겟 승객의 경로 시각화 (빨간색)
            self.plot_route(target_route, networkInfo, color='red', label=f'Target Passenger Route {i+1}')

            plt.xlim(self.x_min, self.x_max)
            plt.ylim(self.y_min, self.y_max)

            # 타겟 승객의 출발지와 도착지 강조
            target_start_node = target_route[0]
            target_end_node = target_route[-1]
            target_start_coords = self.globalVar.getNodeInfoByID(target_start_node)
            target_end_coords = self.globalVar.getNodeInfoByID(target_end_node)
            plt.scatter([target_start_coords[0]], [target_start_coords[1]], color='red', s=100, marker='o', label='Target Start')
            plt.scatter([target_end_coords[0]], [target_end_coords[1]], color='red', s=100, marker='X', label='Target End')

            # 셔틀의 경로 시각화
            self.plot_route(shuttle_route, networkInfo, color=colors[i], label=f'Shuttle Route {i+1}')

            # 셔틀의 출발지 강조
            shuttle_start_node = shuttle_route[0]
            shuttle_start_coords = self.globalVar.getNodeInfoByID(shuttle_start_node)
            plt.scatter([shuttle_start_coords[0]], [shuttle_start_coords[1]], color=colors[i], s=100, marker='o', label=f'Shuttle {i+1} Start')

            plt.title(f"Comparison of Target Route and Shuttle Route {i+1}")
            plt.legend()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            # 파일명 지정 및 저장
            file_name = f"shuttle_route_comparison_{timestamp}_{i+1}.png"
            file_path = os.path.join(output_dir, file_name)
            plt.savefig(file_path)
            plt.close()

            print(f"Route visualization for Shuttle {i+1} saved as {file_path}")

    def plot_route(self, route, networkInfo, color='blue', label=None):
        x_coords = []
        y_coords = []

        for node_id in route:
            node_info = self.globalVar.getNodeInfoByID(node_id)
            x_coords.append(node_info[0])  # x 좌표
            y_coords.append(node_info[1])  # y 좌표

        plt.plot(x_coords, y_coords, color=color, label=label)
        plt.scatter(x_coords, y_coords, color=color)
    
    def load_shortest_paths(self, filepath):
        with open(filepath, 'rb') as f:
            shortest_paths = pickle.load(f)
        return shortest_paths


    '''
        해당 코드는 전체 경로를 보는 코드로 추후 업데이트된다면 사용해야 할듯
    
    def calculate_increasing_boarding_time (self, temp_path, shuttle, networkInfo):
        increased_times = {}
        # curPath에서 curPsgr의 출발지와 도착지를 검색한 후 해당 거리 계산
        # tempPath에서 curPsgr의 출발지와 도착지를 검색한 후 해당 거리 계산 후 앞이랑 비교
        for curPsgr in shuttle.curPsgr:
            # 승객의 출발지와 도착지 노드 가져오기
            curNode = shuttle.curNode
            arrival_node = curPsgr.strArrivalNode
            timenow = self.getTime()
            boarding_time = timenow - curPsgr.departureTime
            
            # tempSchedule의 totalPath에서 새로운 경로 시간 계산
            newPath = temp_path
            if curNode in newPath and arrival_node in newPath:
                new_subpath = newPath[newPath.index(curNode):newPath.index(arrival_node) + 1]
                new_time = self.calculate_total_time(new_subpath, networkInfo)
            else:
                new_time = None  # 승객의 노드가 새로운 경로에 없음

            
            # 경로 시간 증가량 계산 및 리스트에 추가
            if new_time is not None:
                increased_time = (new_time + boarding_time) - curPsgr.expectedArrivalTime
                increased_times[curPsgr.psgrID] = increased_time
                new_time = None
                # if increased_time < 600 and 
        
        return increased_times

    def calculate_waiting_time(self, temp_path, shuttle, networkInfo):
        check_waiting_times = True
        for curDst in shuttle.curDst:
            if curDst[1] == 'BOARDING':
                curPsgr = self.globalVar.getPsgrInfoByID(curDst[2])
                curNode = shuttle.curNode
                departure_node = curPsgr.strDepartureNode
                timenow = self.getTime()
                waiting_time = timenow - curPsgr.waitingStartTime
                new_waiting_time = None
                newPath = temp_path
                if curNode in newPath and departure_node in newPath:
                    new_subpath = newPath[newPath.index(curNode):newPath.index(departure_node) + 1]
                    new_waiting_time = self.calculate_total_time(new_subpath, networkInfo)
                else:
                    print("웨이팅 타임 계산 오류")

                if new_waiting_time is not None and new_waiting_time + waiting_time > 600:
                    check_waiting_times = False
                    new_waiting_time = None
                    break

        return check_waiting_times
    
    '''


