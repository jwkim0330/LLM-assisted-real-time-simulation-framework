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

class Generator(DEVSAtomicModel):
    # 인자 설명 
    # strID: devs 모델의 id, globalVar: Data/GlobalVar.py의 Global 객체, EDService,EDSserviceRate: 모름, genEndTime: 종료 시간?, psgrPercent: 모름   
    def __init__(self, strID, globalVar, EDService, EDServiceRate, genEndTime, psgrPercent):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar #data/GlobalVar.py 에서 GlobalVar 객체를 전역변수로서 선언한 후 가져온다. 
        self.kpi_saver = KPIDataSaver() #중요한 결과를 저장하기 위한 객체 설정
        # GEN_P는 확률 기반 자동 승객생성 
        # GEN-RQ는 요청 기반 수동 승객생성 
        # IDLE은 승객을 생성하지 않는 상태 
        self.stateList = ["GEN_P","GEN_RQ","IDLE"] # 상태 리스트 
        self.state = self.stateList[0] # 처음 상태를 확률 기반 승객 생성 상태로 설정 

       
        # input Ports
        self.addInputPort("Request")
        # output Ports
        self.addOutputPort("Passenger")     #def addOutputPort(self, varOutput):
                                            #    self.outputs.append(varOutput) 즉 output이라는 lst에 Passenger 삽입 

        # self variables
        self.addStateVariable("strID", strID)  #def addStateVariable(self, varState, varStateValue):
                                               #      self.states[varState] = varStateValue, 
                                               # states={"strId":strid} 이런 형식으로 데이터 저장, 이게 의미하는 바가 무엇이지?
                                               # 아마 추측상 상태 천이를 위한 변수와는 달리, 여러 부가 정보를 저장해놓은 딕셔너리일것같다는 생각  

        # 
        # 정확히 어떤 것들을 의미하는지는 모르겠지만, 필요한 여러 정보들을 전역변수로부터 가져온다고 볼 수 있다. -> 정류장 노드,                                        
        self.genInfo = self.globalVar.getGeneratorInfo() #이 함수가 무엇을 하는 함수인지 확인
                                                        #def getGeneratorInfo(self):
                                                        #        return self.genInfo 
                                                        # sef.geninfo에는 아래와 같은 변수가 존재한다. dic형식으로 존재 
                                                        #self.genInfo["validGridList"] = validGridList : 탑승자가 발생할 수 있는 위치 
                                                        #self.genInfo["validGridWeight"] = validGridWeight : 탑승자가 해당 위치에서 발생할 확률 
                                                        #self.genInfo["stopInfo"] = stopInfo , 정류정 노드에 대한 정보 
                                                        # 여기서 validGridlist,validFridWeight,stopinfo가 무엇인지 파악할 필요가 있다. 
        self.validGridList = self.genInfo["validGridList"]
        self.validGridWeight = self.genInfo["validGridWeight"]
        self.stopInfo = self.genInfo["stopInfo"]
        self.genEndTime = genEndTime
        self.psgrPercent = psgrPercent

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
        # genProbability 가 어떻게 쓰이는지 확인해야한다. 
        self.genProbability  = [2,0.5,3,0.3,4,0.2]
        
        #정류장(Stop)에서 특정 개수(stopcount)만큼 무작위 노드를 선택"하는 기능을 수행 -> 랜덤으로 특정 구간에서 승객을 발생시킨다.
        # StopNodeId 에서 몇몇 노드를 선정하여 승객을 발생시킬 노드를 선정 
        # 만약 승객을 랜덤으로 발생시켜 최적 알고리즘을 돌리는 구조라면, 여기서 더 발전해서 특정 구간에서 승객이 많이 발생할떄의 최적 알고리즘은 다를 수 있다, 이러한 경우의 최적 알고리즘을 개발해도 좋을 듯 
        for info in self.stopInfo:
            stop_node_ids = info['stopNodeID']
            stop_count = info['stopCount']
            selected_nodes = random.sample(stop_node_ids, min(len(stop_node_ids), stop_count))
            info['stopNodeID'] = selected_nodes
            
        # load_time_ratios()
        # 주어진 승차(boarding) 및 하차(alighting) 데이터를 기반으로 시간대별 승객 비율(traffic ratios)을 계산하는 기능
        # return hourly_traffic_ratios : 각 시간대별 승객 비율 반환    
        self.hourly_ratios = self.load_time_ratios()

        #simulate_passenger_arrivals: 승객들의 도착시간을 반환하여 timeTable에 저장한다. 이때 time_table은 오름차순으로 정렬 
        self.timeTable = self.simulate_passenger_arrivals(self.hourly_ratios, int(1000 * self.psgrPercent))  # 승객 수 조절 (psgrPercent로 비율 조절) 
        #process_demand_data
        #x	y	00_승차	00_하차	01_승차	01_하차	02_승차	02_하차	03_승차	03_하차	...	23_승차	23_하차
        #1766	1416	0.0022	0.0001	0.0001	0.0022	0.0244	0.0001	0.0200	0.0022	...	0.0001	0.0001
        #1641	8765	0.0001	0.0067	0.0001	0.0467	0.0001	0.0755	0.0022	0.1533	...	0.0022	0.0001
        #2251	7366	0.0156	0.0089	0.1733	0.2844	0.3844	0.1355	0.1555	0.3555	...	0.0333	0.0133
        #여기서 0.0022로 적힌 부분은 전체 수요를 1로 보고 정규화 시킨 결과일듯 
        #이런식의 dataframe 형성하여 특정 시간,특정 노드에 대해서 승차와 하차 데이터 삽입  
        self.dep_arr_data = self.process_demand_data()
        self.arrivalTime = self.timeTable[0]

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
        time.sleep(1)
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
            # getTime 메서드를 쭉 따라가면 최종적으로 DEVSModel.py에서 self.engine 이 존재할거임, 여기서 engine은 클래스 내부에서 정의되지 않았는데
            # 어디에서 들어온 것인지를 파악해보면 객체를 주입당했음을 알 수 있다.
            # gen=Generator()
            # engine=SimulationEngine()
            # gen.getsimulationengine(engine) 이러한 과정을 거쳐서 객체가 주입 된 것이다.
            # def getTime(self):
            #   return self.currentTime 
            if self.getTime() < self.genEndTime :
                self.psgrID = self.psgrID + 1   #psgr을 하나씩 뽑아낼때마다 id의 값을 1씩 증가시킨다 
                #self.genProbability  = [2,0.5,3,0.3,4,0.2], 이전에 genProbability를 다음과 같이 초기화 시켰다. 
                #짝수에 있는 인덱스는 호출 가능한 승객의 수를 의미하고, 홀수에 있는 인덱스는 호출시 확률을 의미한다. 
                #따라서 승객의 수에 따른 확률을 기반으로 승객을 호출하여 psgrNum에 넣는다. 
                #승객의 호출이 발생하면 그에 따라서 승객의 수도 발생시키고 해당 승객의 수를 psgrNuM에 저장한다. 
                psgrNum = int(np.random.choice(self.genProbability[0::2], p=self.genProbability[1::2]))
                self.psgrCount = self.psgrCount + psgrNum #psgr count는 무엇을 의미하지? 
                
                #timeTable은 승객들의 도착 시간을 적어놓은 리스트,timetable이 오름차순으로 정렬되어 있으므로 그 다음에 발생할 승객들의 시간 흐름을 진행시킨다. 
                if len(self.timeTable) != 1:
                    self.arrivalTime = self.timeTable[1] - self.timeTable[0]
                    self.timeTable.pop(0)
                else :
                    self.arrivalTime = 1
                    if self.timeTable:
                        self.timeTable.pop(0)     #리스트가 요소가 1개만 있다면 마지막 승객이므로 arrivalTime을 무한대로 적용해서 시뮬레이션 종료 

                current_hour = self.getTime() // 3600
                dep_hour_str = f"{current_hour:02d}_승차"  # 예: '00_승차'
                arr_hour_str = f"{current_hour:02d}_하차"  # 예: '00_승차' 여기서 00 은 시간이다 도착 시간과 출발 시간을 표시

                #기존의 데이터를 기반으로 출발 위치와 도착 위치의 좌표 설정 
                dep_x, dep_y = self.select_node(dep_hour_str)
                arr_x, arr_y = self.select_node(arr_hour_str)
                
                #edsservice는 특별 서비스를 의미한다. 더 빠른 전송이라든지, 우리가 할 분야에선 필요가 없을 듯 함 
                if self.EDService == True: 
                    if random.random() < self.EDServiceRate :
                        psgrEDS = True
                    else :
                        psgrEDS = False
                else :
                    psgrEDS = False

                dep_node = self.globalVar.add_dynamic_node(dep_x, dep_y)
                arr_node = self.globalVar.find_nearest_nodes(arr_x, arr_y)
                arr_node = arr_node[0]
                is_auto_generated=True
                # org_node_lst = self.globalVar.getNearestNode(dep_node, 10)
                

                #def setTargetPsgr(self, psgrID, psgrNum, DNode, ANode, psgrEDS, time):
                #   self.psgrWaitingQueue[psgrID] = Passenger(psgrID, psgrNum, DNode, ANode, psgrEDS, time)
                #self.psgrWaitingQueue={} 이고 key=psgrID,value:Passenger, 여기서 Passenger는 승객 객체, GlobalVar.py에서 확인 가능 
                # 즉 전역변수 psgrwaitingqueue에 승객 객체를 넣어서 대기하도록 한다. 
                self.globalVar.setTargetPsgr(self.psgrID, psgrNum, dep_node, arr_node, psgrEDS, self.getTime(),is_auto_generated)
                
                #데이터 저장을 위한 코드 
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'psgrNum': psgrNum})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node' : dep_node})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'dep_node_expanded' : (float(dep_x/10000+126),float(dep_y/10000+37))})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'arr_node' : arr_node})
                    calltime = self.getTime()
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, self.psgrID, {'calltime' : calltime})
                else:
                    pass
                

                #def addOutputEvent(self, varOutput, varMessage):
                #   self.engine.addEvent(Event(self, varOutput, varMessage))
                #  
                # -> 여기서 engine은 SimulationEngine 객체이다. (주입을 통해서 객체 참조를 하게 되었다)
                # -> self가 나타내는 객체는 generator 객체이다. why? -> generator 객체가 addOutputEvent를 호출하게 되었고 따라서 self 는 generator객체를 의미한다.
                # 착각한 부분 genertor객체는 devsAtomic을 상속받았는데 다시 Atomic 모델의 함수를 호출하면 누가 객체이지? 라는 의문
                # 상속 받았으므로 genertor는 devsAtomic을 참조하는 것이 아닌 확장이다. 따라서 atomic의 함수를 전부 사용 가능하고 그 주체는 객체 그 자신이다. 
                # 이 함수에서는 이벤트 객체를 정의함과 동시에 전달을 한다. 정의된 이벤트는 아래와 같다. 

                #model=self(여기서 self는 generator 객체),varOutput="Passenger",varMessage=self.psrgID 이다. 
                #class Event:
                #   def __init__(self,model,varOutput,varMessage,blnResolutionChange = False):
                
                #위와 같이 정의된 event가 
                #self(generator).engine(simulator).queueEvent 에 들어가게 된다. 이때 queue= [] 형식을 가진다. 
                
                #def addEvent(self,event):
                #   self.queueEvent.append(event) -> 여기서 event 는 Event.py의 event객체이다. 
                
                # 그러면 외부로 보내는 단 하나의 값 passenger는 
                # generator.engine.queueEvent에서 확인 가능하고, 그 다음 코드에서 이걸 어떻게 사용하는지 확인할 필요가 있다. 
                self.addOutputEvent("Passenger", self.psgrID)
                self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} generated #{} to #{}".format(self.getTime(), self.getStateValue("strID"), self.psgrID,psgrNum,dep_node, arr_node))
            return True
        elif self.state == "IDLE":
            # IDLE 상태에서는 출력 이벤트가 발생하지 않아야 하므로, 아무것도 하지 않고 True 반환
            return True

        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False


    
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
