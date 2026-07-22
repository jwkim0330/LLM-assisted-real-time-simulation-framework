import pandas as pd
import os

class KPIDataSaver:
    # [핵심] 싱글톤 패턴을 위한 클래스 변수
    _instance = None

    def __new__(cls, *args, **kwargs):
        # 파이썬 어디에서 KPIDataSaver()를 부르든, 무조건 똑같은 객체 1개만 반환하도록 강제함
        if not isinstance(cls._instance, cls):
            cls._instance = super(KPIDataSaver, cls).__new__(cls, *args, **kwargs)
            # 최초 1회만 메모리 바구니 생성
            cls._instance.passengers_dict = {}
            cls._instance.vehicle_list = []
        return cls._instance

    def __init__(self):
        # __init__은 객체가 불릴 때마다 실행되므로, 여기서 초기화하면 데이터가 날아갑니다. 
        # 따라서 여기는 비워둡니다.
        pass

    def Passengers_data(self, scenario_id, passenger_id, data):
        key = (scenario_id, passenger_id)
        if key not in self.passengers_dict:
            self.passengers_dict[key] = {
                'scenario_info': scenario_id,
                'passenger_id': passenger_id
            }
        self.passengers_dict[key].update(data)

    def vehicle_data(self, scenario_id, current_time, shuttle_id, shuttle_state,
                     cur_dst, cur_node, cur_path, cur_psgr, cur_psgr_num):
        vehicle_info = {
            'scenario_info': scenario_id,
            'currenttime': current_time,
            'shuttle_id': shuttle_id,
            'shuttle_state': shuttle_state,
            'cur_dst': cur_dst,
            'cur_node': cur_node,
            'cur_path': cur_path,
            'cur_psgr': cur_psgr,
            'cur_psgr_num': cur_psgr_num
        }
        self.vehicle_list.append(vehicle_info)

    def save_and_clear(self, output_dir, seed_num):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if self.passengers_dict:
            df_passengers = pd.DataFrame(list(self.passengers_dict.values()))
            passengers_file = f"{output_dir}/passengers_kpi_seed_{seed_num}.csv"
            df_passengers.to_csv(passengers_file, index=False, encoding='utf-8-sig')

        if self.vehicle_list:
            df_vehicles = pd.DataFrame(self.vehicle_list)
            vehicles_file = f"{output_dir}/vehicle_kpi_seed_{seed_num}.csv"
            df_vehicles.to_csv(vehicles_file, index=False, encoding='utf-8-sig')

        # 다음 시드를 위해 바구니를 깨끗하게 비움
        self.passengers_dict.clear()
        self.vehicle_list.clear()

    def __del__(self):
        pass