# 승객의 탑승 요청을 실시간으로 받아서 generator에 전달하는 모듈
from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import threading, json, socket

class recv_request_server(DEVSAtomicModel):
    def __init__(self, strID, globalVar):
        super().__init__(strID)
        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["OPEN","SEND","ASSIGN","CLOSE"]
        self.state = self.stateList[0]
        self.dataqueue = []
        self.client_queue=[] #멀티스레드로 생성된 클라이언트 관리하는 큐 
        self.Awaiting_Dispatch_Queue=[] #클라이언트의 요청에 대한 응답을 기록하는 큐 

        # input ports
        self.addInputPort("Result_Notification")
        # Output ports
        self.addOutputPort("Request")

        # self variables
        self.addStateVariable("strID", strID)

        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def start_server(self):
        self.host = "127.0.0.1"
        self.port = 8888
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"서버가 {self.host}:{self.port}에서 대기 중...")

        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"{addr}에서 연결됨")

                # 새 클라이언트가 들어올 때마다 별도 스레드에서 처리
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
                self.client_queue.append(client_socket)
            except Exception as e:
                print(f"[서버:{addr}] 오류: {e}")
                break


    def handle_client(self, client_socket, addr): 
        """
        각 클라이언트의 요청을 받아 dataqueue에 저장
        """
        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    print(f"{addr} 연결 종료")
                    break
                self.dataqueue.append(data)
                print(f"{addr} -> 수신 데이터: {data}")

        except Exception as e:
            print(f"[서버:{addr}] 오류: {e}")


            

    def funcExternalTransition(self, strPort, event):
        #"RESULT_NOTOFICATION" 이라는 포트는 요청을 보낸 경우에만 사용하도록 설계,따라서 해당 포트로 정보를 받는 경우는 state=ASSiGN
        if strPort=="Result_Notification":
            self.Awaiting_Dispatch_Queue.append(event)
            self.state="ASSIGN"
    

    def funcInternalTransition(self):
        ## OPEN 상태인 경우 데이터가 들어오면 SEND로 변환
        if self.state=="ASSIGN":
            self.state="OPEN"
        elif self.client_queue:
            self.state="SEND"
            return True
        else:
            return True

    def funcOutput(self):
        if self.state == "OPEN":
            if self.dataqueue:
                recv_data = self.dataqueue.pop(0)
                try:
                    parsed_data = json.loads(recv_data)
                    self.globalVar.printTerminal("######################데이터를 전송 ############################")
                    self.addOutputEvent("Request", parsed_data)
                    return True
                except json.JSONDecodeError:
                    print("JSON 파싱 오류, raw_data:", recv_data)
                    return True
            else:
                return True
        elif self.state=="ASSIGN":
            data=self.Awaiting_Dispatch_Queue.pop(0)
            if data["is_assigned_shuttle"]==True:
                ShuttleID=data["shuttle_id"]
                passenger_ID=data["passenger_ID"]
                send_data = {"ShuttleID": ShuttleID,"passenger_ID":passenger_ID}

            elif data["is_assigned_shuttle"]==False:
                send_data = {"message": "assign error : 적절한 위치에서 차량을 호출해주세요"}
                  
            
            if self.client_queue:  # 클라이언트 소켓이 저장된 큐가 비어있지 않은지 확인
                    client_socket = self.client_queue.pop(0)
                    try:
                        # 데이터를 JSON 문자열로 변환 후, utf-8로 인코딩하여 전송
                        message = json.dumps(send_data)
                        client_socket.send(message.encode('utf-8'))
                        print(f"{client_socket.getpeername()}에게 데이터 전송 완료")
                    except Exception as e:
                        print(f"데이터 전송 중 오류 발생: {e}")
                
            else:
                print("전송할 클라이언트 소켓이 없습니다.")
            
            return True
        elif self.state=="OPEN":
            return True
        else:
            print("ERROR at recv_request_server OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False


    def funcTimeAdvance(self):
        if self.state=="OPEN":
            return 1
        elif self.state=="SEND":
            return 999999999 
        elif self.state=="ASSIGN":
            return 0 
        elif self.state=="CLOSE":
            return 999999999
