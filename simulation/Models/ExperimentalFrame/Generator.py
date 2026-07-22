from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import numpy as np
import random
import math
import pandas as pd
import time 
import socket
import threading
import json
import os 

class Generator(DEVSAtomicModel):
    # 인자 설명 
    # strID: devs 모델의 id, globalVar: Data/GlobalVar.py의 Global 객체, EDService,EDSserviceRate: 모름, genEndTime: 종료 시간?, psgrPercent: 모름   
    def __init__(self, strID, globalVar, EDService, EDServiceRate, genEndTime, psgrPercent):
        super().__init__(strID)

        current_seed = int(os.environ.get("CURRENT_SEED", 42))
        np.random.seed(current_seed)
        random.seed(current_seed)
        # set Global Variables
        self.globalVar = globalVar 
        self.kpi_saver = KPIDataSaver() 
        self.stateList = ["GEN_P","GEN_RQ","IDLE"] 
        self.state = self.stateList[0] 

       
        # input Ports
        self.addInputPort("Request")
        # output Ports
        self.addOutputPort("Passenger")     

        # self variables
        self.addStateVariable("strID", strID)  

        self.genInfo = self.globalVar.getGeneratorInfo() 
                                                      
        self.validGridList = self.genInfo["validGridList"]
        self.validGridWeight = self.genInfo["validGridWeight"]
        self.stopInfo = self.genInfo["stopInfo"]
        self.genEndTime = genEndTime
        
        #EDService 지원 여부 
        self.EDServiceRate = EDServiceRate
        if self.EDServiceRate == 0:
            self.EDService = False
        else :
            self.EDService = True

        # Generator 클래스 초기화 시
        self.genEndTime = float('inf')  # genEndTime을 무한대로 설정
        
        # variables
        self.psgrID = 0 #승객의 ID
        self.psgrCount = 0 # 누적 승객 수 
        self.RQpassengerlst=[]


        ## 승객 자동 생성을 위한 로직 
        self.genProbability  = [2,0.5,3,0.3,4,0.2]
        
        for info in self.stopInfo:
            stop_node_ids = info['stopNodeID']
            stop_count = info['stopCount']
            selected_nodes = random.sample(stop_node_ids, min(len(stop_node_ids), stop_count))
            info['stopNodeID'] = selected_nodes
            
        self.hourly_ratios = self.load_time_ratios()

        # simulate_passenger_arrivals: 승객들의 도착시간을 반환
        self.timeTable = self.simulate_passenger_arrivals(self.hourly_ratios, 1000)  # 승객 수 조절 
        
        # [수정됨: 순서 변경] dep_arr_data를 먼저 생성해야 select_node에서 사용 가능합니다.
        self.dep_arr_data = self.process_demand_data()

        # [추가됨] 배경 트래픽(Background Traffic) 미리 생성 (Pre-generation)
        self.background_traffic = []
        
        # np.random.seed(42) # 필요시 시드 고정

        for arrival_time in self.timeTable:
            # 1. 시간대 계산
            current_hour = arrival_time // 3600
            dep_hour_str = f"{current_hour:02d}_승차"
            arr_hour_str = f"{current_hour:02d}_하차"
            
            # 2. 위치 결정 (이제 dep_arr_data가 있으므로 에러가 나지 않습니다)
            dep_x, dep_y = self.select_node(dep_hour_str)
            arr_x, arr_y = self.select_node(arr_hour_str)
            
            # 3. 인원수 결정
            psgrNum = int(np.random.choice(self.genProbability[0::2], p=self.genProbability[1::2]))
            
            # 4. EDS 서비스 여부 결정
            psgrEDS = False
            if self.EDService: 
                if random.random() < self.EDServiceRate :
                    psgrEDS = True
            
            # 5. 저장
            psgr_info = {
                "time": arrival_time,
                "dep_x": dep_x,
                "dep_y": dep_y,
                "arr_x": arr_x,
                "arr_y": arr_y,
                "psgrNum": psgrNum,
                "psgrEDS": psgrEDS
            }
            self.background_traffic.append(psgr_info)

        # [실험 3: 다중 시나리오 및 다중 분포 완벽 통제 주입 로직]
        
        self.target_scenario = os.environ.get("TARGET_SCENARIO", "HOLIDAY").upper()
        self.target_dist = os.environ.get("TARGET_DIST", "HILS_BURST").upper()
        
        scenarios = {
            "FESTIVAL": {
                "time": 1500, 
                "dep_x": 126.83739657110384, "dep_y": 37.29762586758092, 
                "arr_x": 126.85369272696458, "arr_y": 37.30999131775141
            },
            "LUNCH": {
                "time": 1500, 
                "dep_x": 126.8351539884716, "dep_y": 37.29677579144293, 
                "arr_x": 126.83856396910281, "arr_y": 37.316062635101254
            },
            "HOLIDAY": {
                "time": 1500, 
                "dep_x": 126.8352535886907, "dep_y": 37.29247798602247, 
                "arr_x": 126.85716970086038, "arr_y": 37.29072240793255
            }
        }
        
        if self.target_scenario not in scenarios:
            raise ValueError(
                f"Unknown TARGET_SCENARIO={self.target_scenario!r}. "
                f"Choose one of: {sorted(scenarios)}"
            )
        valid_distributions = {"HILS_BURST", "MATH_UNIFORM", "MATH_POISSON"}
        if self.target_dist not in valid_distributions:
            raise ValueError(
                f"Unknown TARGET_DIST={self.target_dist!r}. "
                f"Choose one of: {sorted(valid_distributions)}"
            )

        target_info = scenarios[self.target_scenario]
        base_time = target_info["time"]
        
        local_prng = np.random.RandomState(42)
        
        for i in range(10):
            if self.target_dist == "HILS_BURST":
                inject_time = base_time
            elif self.target_dist == "MATH_UNIFORM":
                inject_time = base_time + (i * 30)
            elif self.target_dist == "MATH_POISSON":
                if i == 0:
                    inject_time = base_time
                else:
                    inject_time = base_time + int(np.sum(local_prng.exponential(scale=30, size=i)))
                    
            # [중요 버그 수정] 기존 코드의 좌표계(스케일)에 맞게 10000을 곱하는 전처리 적용
            scaled_dep_x = (target_info["dep_x"] - 126) * 10000
            scaled_dep_y = (target_info["dep_y"] - 37) * 10000
            scaled_arr_x = (target_info["arr_x"] - 126) * 10000
            scaled_arr_y = (target_info["arr_y"] - 37) * 10000

            psgr_info = {
                "time": inject_time,
                "dep_x": scaled_dep_x,
                "dep_y": scaled_dep_y,
                "arr_x": scaled_arr_x,
                "arr_y": scaled_arr_y,
                "psgrNum": 1,
                "psgrEDS": False
            }
            self.background_traffic.append(psgr_info)
            
        # 시간순으로 전체 명단을 다시 정렬하여 엔진 점프 오류 방지
        self.background_traffic = sorted(self.background_traffic, key=lambda x: x["time"])
        # ======================= 여기까지 복사해서 삽입 =======================

        # 첫 번째 도착 시간 설정 (이 아래부터는 기존 코드 그대로 둡니다)
        if self.background_traffic:
            self.arrivalTime = self.background_traffic[0]["time"]
        else:
            self.arrivalTime = float('inf')
        # ----------------------------
        #     
        # 첫 번째 도착 시간 설정
        if self.background_traffic:
            self.arrivalTime = self.background_traffic[0]["time"]
        else:
            self.arrivalTime = float('inf')

    #외부의 서버로부터 승객의 요청 받기 
    def funcExternalTransition(self, strPort, objEvent):
        if strPort=="Request":
            data=objEvent
            self.RQpassengerlst.append(data)
            self.globalVar.printTerminal("######################데이터를 받음 ############################")
            self.state="GEN_RQ"
            return True
        else:
            return False
    
    #fcunExternalTransition에서 얻어온 값을 가지고 승객 객체를 만든 후 해당 값을 queue에 넣어야한다. 
    # 혹은 init에서 초기화한 서버를 통해서 값을 가져와야한다. 
    def funcOutput(self):
        #time.sleep(1)
        if self.state == "GEN_RQ":
            self.globalVar.printTerminal("######################받은 데이터 처리 확인############################")
            data=self.RQpassengerlst.pop(0)

            self.dep_x = (data["dep_x"]-126)*10000
            self.dep_y = (data["dep_y"]-37)*10000
            self.arr_x = (data["arr_x"]-126)*10000
            self.arr_y = (data["arr_y"]-37)*10000
            self.psgrNum = data["psgrNum"]
            self.psgrID = self.psgrID + 1   #psgr을 하나씩 뽑아낼때마다 id의 값을 1씩 증가시킨다 
            self.psgrCount = self.psgrCount + self.psgrNum #psgr count 지금까지의 누적 승객 수 계산 
            is_auto_generated=False
            ## 사용 안할거임 오류 방지를 위해서 남겨놓은 것 
            psgrEDS = False
            
            #출발해야하는 노드와 도착해야하는 노드를 globalVar에 저장 
            dep_node = self.globalVar.add_dynamic_node(self.dep_x, self.dep_y)
            arr_node = self.globalVar.find_nearest_nodes(self.arr_x, self.arr_y)
            arr_node = arr_node[0] #arr_node는 리스트 형식으로 노드와 가장 가까운 애들부터 정렬되어있다. 이 중 가장 가까운 노드가 [0] 에 있다

            # 전역변수 psgrwaitingqueue에 승객 객체를 넣어서 대기하도록 한다. 여기서 passenger class를 호출해서 승객 객체를 만든다. 
            self.globalVar.setTargetPsgr(self.psgrID, self.psgrNum, dep_node, arr_node, psgrEDS, self.getTime(),is_auto_generated)
                
            #데이터 저장을 위한 코드 
            if self.globalVar.isDBsave == True:
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'psgrNum': self.psgrNum})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node' : dep_node})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node_expanded' : (float(self.dep_x/10000+126),float(self.dep_y/10000+37))})
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'arr_node' : arr_node})
                calltime = self.getTime()
                self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'calltime' : calltime}) 
            
            #def addOutputEvent(self, varOutput, varMessage):
            #   self.engine.addEvent(Event(self, varOutput, varMessage))
            #def addEvent(self,event):
            #   self.queueEvent.append(event) -> queueEvent=[event객체]
            #class Event:
            #   def __init__(self,model,varOutput,varMessage,blnResolutionChange = False):
            #       self.modelSender = model
            #       self.portSender = varOutput
            #       self.message = varMessage
            #       self.blnResolutionChange = blnResolutionChange
            # Event: modelsender=self(generator), portsender:"Passenger",message=self.psgrID 이라는 이벤트 객체를 simulationengine queueevent에 저장 
            self.addOutputEvent("Passenger", self.psgrID)
            self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} generated #{} to #{}".format(self.getTime(), self.getStateValue("strID"), self.psgrID,self.psgrNum,dep_node, arr_node))
            return True
        
        elif self.state == "GEN_P":
            # [수정됨] 런타임 난수 생성 제거 -> 미리 만든 리스트에서 꺼내오기만 함
            
            # 리스트에 남은 승객이 있는지 확인
            if self.background_traffic:
                # 1. 대기열에서 승객 정보 꺼내기
                p_info = self.background_traffic.pop(0)
                
                # 2. 정보 매핑
                self.psgrID = self.psgrID + 1
                psgrNum = p_info["psgrNum"]
                self.psgrCount = self.psgrCount + psgrNum
                
                dep_x = p_info["dep_x"]
                dep_y = p_info["dep_y"]
                arr_x = p_info["arr_x"]
                arr_y = p_info["arr_y"]
                psgrEDS = p_info["psgrEDS"]
                
                # 3. 노드 설정 (기존 로직 유지)
                dep_node = self.globalVar.add_dynamic_node(dep_x, dep_y)
                # find_nearest_nodes는 리스트를 반환하므로 [0]으로 첫번째 요소 선택
                arr_node_list = self.globalVar.find_nearest_nodes(arr_x, arr_y)
                arr_node = arr_node_list[0]
                
                is_auto_generated = True

                # 4. GlobalVar에 승객 등록
                self.globalVar.setTargetPsgr(self.psgrID, psgrNum, dep_node, arr_node, psgrEDS, self.getTime(), is_auto_generated)
                
                # 5. 데이터 저장 (KPI)
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'psgrNum': psgrNum})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node' : dep_node})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node_expanded' : (float(dep_x/10000+126), float(dep_y/10000+37))})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'arr_node' : arr_node})
                    calltime = self.getTime()
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'calltime' : calltime})
                else:
                    pass

                # 6. 이벤트 전송
                self.addOutputEvent("Passenger", self.psgrID)
                self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} generated #{} to #{}".format(self.getTime(), self.getStateValue("strID"), self.psgrID, psgrNum, dep_node, arr_node))

                # 7. [중요] 다음 승객까지의 시간(Time Advance) 계산
                if self.background_traffic:
                    next_arrival_time = self.background_traffic[0]["time"]
                    # 다음 도착 예정 시간 - 현재 시간 = 대기해야 할 시간(sigma)
                    self.arrivalTime = next_arrival_time - self.getTime()
                else:
                    # 더 이상 승객이 없으면 무한대 대기
                    self.arrivalTime = float('inf') 

            return True


    
    #내부 천이 분기점 도달 시, 데이터가 존재하면 GEN 상태로 천이, 그것이 아니라면 WAIT 상태 유지
    # 이 코드는 내부 천이 함수를 외부 천이 함수처럼 사용중,   
    def funcInternalTransition(self):
        if self.RQpassengerlst:
            self.state=self.stateList[1]
            return True
        if len(self.timeTable) != 0 :
            self.state = self.stateList[0]
            return True
        else:
            psgr = self.globalVar.getPsgrInfoByID(self.psgrID)
            psgr.setlastPsgr()
            self.state = self.stateList[2]
            return True
   
 

    # 
    def funcTimeAdvance(self):
        if self.state == "GEN_P":
            return self.arrivalTime   
        
        elif self.state=="GEN_RQ":
            return 0
        
        elif self.state=="IDLE":
            return 9999999 # 원래는 무한대로 해야 하는데, wallclock문제로 10으로 해놓았다 
        

            


    
    #############################################################################################
    #### 승객 생성을 위한 메서드 

    #rate_per_hour: 시간당 도착률,total_time: 전체 시뮬레이션 시간, seed:난수 발생 시드 를 input으로 넣어서
    #total_time보다 작은 도착 시간을 리스트에 삽입한다. 
    def simulate_arrival_times(self, rate_per_hour, total_time, seed):
        np.random.seed(seed)
        mean_arrival_rate = 3600 / rate_per_hour
        inter_arrival_times = np.random.exponential(mean_arrival_rate, int(rate_per_hour * total_time / 3600))
        arrival_times = np.cumsum(inter_arrival_times)
        arrival_times = arrival_times[arrival_times <= total_time]
        return arrival_times
        
    # 총 승객수와 교통혼잡도를 반영하여 각 승객들의 도착 시간을 포아송 분포로 반환하게 된다. 
    def simulate_passenger_arrivals(self, hourly_traffic_ratios, total_passengers):
        all_arrivals = []
        
        for hour, ratio in hourly_traffic_ratios.items():
            if ratio > 0:
                hour_index = int(hour[:2])  # 'XX(승차)'에서 'XX' 부분 추출
                expected_passengers = total_passengers * ratio
                lambda_hour = expected_passengers / 3600  # 1시간 = 3600초

                # 포아송 프로세스를 사용하여 도착 시간 생성
                arrival_time = hour_index * 3600  # 시간대의 시작 시간
                while arrival_time < (hour_index + 1) * 3600:
                    inter_arrival_time = np.random.exponential(1 / lambda_hour)
                    arrival_time += inter_arrival_time
                    if arrival_time >= (hour_index + 1) * 3600:
                        break
                    all_arrivals.append(int(arrival_time))

        all_arrivals.sort()  # 도착 시간 정렬

        # 동일한 시간에 도착하는 승객들의 시간을 미세하게 조정
        for i in range(1, len(all_arrivals)):
            if all_arrivals[i] <= all_arrivals[i-1]:
                all_arrivals[i] = all_arrivals[i-1] + 1

        return all_arrivals

    #주어진 승차(boarding) 및 하차(alighting) 데이터를 기반으로 **시간대별 승객 비율(traffic ratios)**을 계산하는 기능
    #return hourly_traffic_ratios, 각 시간대별 승객 비율 반환 
    def load_time_ratios(self):


        # 시간대별로 정규화된 비율 데이터를 로드합니다.
        # 실제 데이터로 교체해야 합니다.
        # 데이터 형식은 딕셔너리로, 키는 시간대(정수), 값은 해당 시간대의 비율 리스트입니다.
        # 예시 데이터를 사용합니다.
        data = pd.read_excel('JSON/Demand.xlsx', header=1)
        demand_data = pd.DataFrame(data)

        boarding_columns = [col for col in demand_data.columns if '승차' in col and 'Unnamed' not in col]
        alighting_columns = [col for col in demand_data.columns if '하차' in col and 'Unnamed' not in col]

        # 승차와 하차 데이터 선택
        boarding_data = demand_data[boarding_columns].astype(float)
        alighting_data = demand_data[alighting_columns].astype(float)

        # 승차와 하차 데이터의 인덱스 정렬 (하차 시간 열 이름에서 '승차'로 변경하여 일치시키기)
        alighting_data.columns = boarding_data.columns

        # 승차와 하차 데이터 합산
        total_traffic_data = boarding_data + alighting_data

        # 각 시간대별 승객 수의 총합 계산
        hourly_total_traffic = total_traffic_data.sum()

        # 각 시간대의 승객 비율 계산 (총 승객 수 대비 각 시간대 승객 수의 비율)
        total_traffic_sum = hourly_total_traffic.sum()
        hourly_traffic_ratios = hourly_total_traffic / total_traffic_sum

        # 결과 출력
        hourly_traffic_ratios

        return hourly_traffic_ratios

    #process_demand_data
    #x	y	00_승차	00_하차	01_승차	01_하차	02_승차	02_하차	03_승차	03_하차	...	23_승차	23_하차
    #1766	1416	0.0022	0.0001	0.0001	0.0022	0.0244	0.0001	0.0200	0.0022	...	0.0001	0.0001
    #1641	8765	0.0001	0.0067	0.0001	0.0467	0.0001	0.0755	0.0022	0.1533	...	0.0022	0.0001
    #2251	7366	0.0156	0.0089	0.1733	0.2844	0.3844	0.1355	0.1555	0.3555	...	0.0333	0.0133
    #여기서 0.0022로 적힌 부분은 전체 수요를 1로 보고 정규화 시킨 결과일듯 
    #이런식의 dataframe 형성하여 특정 시간,특정 노드에 대해서 승차와 하차 데이터 삽입 
    def process_demand_data(self):
        # 데이터 불러오기
        data = pd.read_excel('JSON/Demand.xlsx', header=1)
        df = pd.DataFrame(data)

        # 위도와 경도를 기반으로 x, y 좌표 계산
        df['y'] = ((df['위도'] - 37) * 10000).astype(int)
        df['x'] = ((df['경도'] - 126) * 10000).astype(int)

        # 새 DataFrame 초기화
        new_df = pd.DataFrame()
        new_df['x'] = df['x']
        new_df['y'] = df['y']

        # 모든 시간대에 대한 승차 및 하차 데이터 추가
        for time in range(24):
            hour_str = f"{time:02d}"  # 시간을 '00', '01', ..., '23' 형식으로 포맷
            boarding_col = f"{hour_str}(승차)"
            alighting_col = f"{hour_str}(하차)"
            
            # 승차 및 하차 데이터가 존재하는지 확인하고 추가
            if boarding_col in df.columns and alighting_col in df.columns:
                boarding_data = df[boarding_col].replace(0, 0.0001)
                alighting_data = df[alighting_col].replace(0, 0.0001)
                new_df[f"{hour_str}_승차"] = boarding_data
                new_df[f"{hour_str}_하차"] = alighting_data

        # 결과 DataFrame 반환
        return new_df


    #hour_str을 넣으면 승차 데이터를 기반으로 출발 위치를 설정한다.  
    def select_node(self, hour_str):
        #dep_arr_data:시간대별 승하차 비율 데이터
        if hour_str in self.dep_arr_data.columns:
            # 시간대에 맞는 승차 데이터로 가중치 설정
            valid_data = self.dep_arr_data[['x', 'y', hour_str]]
            
            # 가중치에 따라 출발 위치 선택
            selected_stop = valid_data.sample(weights=valid_data[hour_str], n=1)
            node_x = selected_stop['x'].values[0]
            node_y = selected_stop['y'].values[0]
            jitter = 10  # 변동 범위 조정 가능
            node_x += random.uniform(-jitter, jitter)
            node_y += random.uniform(-jitter, jitter)

        else:
            # 데이터 없음 시 무작위 위치
            node_x = random.uniform(430, 1430)
            node_y = random.uniform(1510, 2280)
        
        return node_x, node_y
