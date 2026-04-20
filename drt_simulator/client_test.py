import socket
import json
import time
import random

def send_passenger_data(host, port):
    # 소켓 생성
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # 서버에 연결
        client_socket.connect((host, port))
        print(f"서버({host}:{port})에 연결되었습니다.") 
        
        # 승객 데이터 전송 (예: 1회 전송)
        for i in range(100):
            # 승객 데이터 랜덤 생성
            # 승객 배차 성공 버전 
            
            #dep_x = 126.8545241  
            #dep_y = 37.29266 #감골도서관 

            dep_x = 126.8394712
            dep_y = 37.3110838

            #dep_x = 126.8274888 ##안산 호수공원 
            #dep_y = 37.2977056

            #dep_x = 126.8220475 ## 양지 고등학교 
            #dep_y = 37.309452

            ##ep_x = 126.85115175843727 ## 초당 초등학교 
            ##dep_y = 37.2856917081450


            arr_x = 126.83518867886451 # 한대앞역
            arr_y = 37.29638388900675 
               
        

            psgrNum = 7
            # 데이터 구성 (JSON 형식)
            data = {
                "dep_x": dep_x,    
                "dep_y": dep_y,    
                "arr_x": arr_x,    
                "arr_y": arr_y,    
                "psgrNum": psgrNum 
            }
            
            # JSON 문자열로 변환 및 전송
            json_data = json.dumps(data)
            client_socket.sendall(json_data.encode('utf-8'))
            print(f"[전송] {json_data}")
            
            time.sleep(0.1)  # 지속 송신을 위한 대기 시간
            time.sleep(17)
        # 데이터 전송 완료 후 서버 응답 대기
        print("서버 응답 대기 중...")
        response_data = client_socket.recv(1024)
        if not response_data:
            print("서버로부터 응답이 없습니다.")
        else:
            response_text = response_data.decode('utf-8').strip()
            print(f"[디버그] 수신 원문: {response_text}")

            try:
                
                # 서버가 전송한 데이터 형식에 따른 출력 처리
                print(response_text)
            except json.JSONDecodeError as e:
                print("수신 데이터 JSON 파싱 오류:", e)
    
    except KeyboardInterrupt:
        print("\n사용자 종료 요청. 클라이언트를 종료합니다.")
    
    except Exception as e:
        print(f"클라이언트 오류: {e}")
    
    finally:
        client_socket.close()
        print("서버 연결이 종료되었습니다.")

# 클라이언트 실행
if __name__ == "__main__":
    HOST = "127.0.0.1"  # Generator의 서버 IP
    PORT = 8888         # Generator의 서버 포트
    
    send_passenger_data(HOST, PORT)
