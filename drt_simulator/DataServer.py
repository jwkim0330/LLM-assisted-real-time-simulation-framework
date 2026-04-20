import os
import psycopg2

class KPIDataSaver:
    def __init__(self):
        self.dbname = os.getenv("DB_NAME", "test_drt")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.connection = self.connect()
        if self.connection:
            self.cursor = self.connection.cursor()
        else:
            self.cursor = None
        self.passengers_table_name = "passengers_kpi"
        self.vehicle_table_name = "vehicle_kpi"

    def connect(self):
        try:
            conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            return conn
        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def delete_all_data(self):
        if not self.connection:
            print("Database connection is not established.")
            return
        try:
            self.cursor.execute(f"DELETE FROM {self.passengers_table_name}")
            self.cursor.execute(f"DELETE FROM {self.vehicle_table_name}")
            self.connection.commit()
        except Exception as e:
            print(f"Error occurred in delete_all_data: {e}")
            if self.connection:
                self.connection.rollback()

    def Passengers_data(self, scenario_id, passenger_id, data):
        if not self.connection:
            print("Database connection is not established.")
            return
        
        try:
            self.cursor.execute(
                f"SELECT 1 FROM {self.passengers_table_name} WHERE scenario_info = %s AND passenger_id = %s",
                (scenario_id, str(passenger_id))
            )
            exists = self.cursor.fetchone()

            if not exists:
                # Insert
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                values = [str(v) for v in data.values()]
                insert_query = (
                    f"INSERT INTO {self.passengers_table_name} "
                    f"(scenario_info, passenger_id, {columns}) "
                    f"VALUES (%s, %s, {placeholders})"
                )
                self.cursor.execute(insert_query, (scenario_id, str(passenger_id), *values))
            else:
                # Update
                updates = ', '.join([f"{k} = %s" for k in data.keys()])
                values = [str(v) for v in data.values()]
                update_query = (
                    f"UPDATE {self.passengers_table_name} "
                    f"SET {updates} "
                    f"WHERE scenario_info = %s AND passenger_id = %s"
                )
                self.cursor.execute(update_query, (*values, scenario_id, str(passenger_id)))

            self.connection.commit()
        except Exception as e:
            print(f"Error occurred in Passengers_data: {e}")
            if self.connection:
                self.connection.rollback()  # <--- ROLLBACK 추가

    def vehicle_data(self, scenario_id, current_time, shuttle_id, shuttle_state,
                     cur_dst, cur_node, cur_path, cur_psgr, cur_psgr_num):
        if not self.connection:
            print("Database connection is not established.")
            return
        
        try:
            columns = 'scenario_info, currenttime, shuttle_id, shuttle_state, cur_dst, cur_node, cur_path, cur_psgr, cur_psgr_num'
            placeholders = ', '.join(['%s'] * 9)
            values = (
                str(scenario_id),
                str(current_time),
                str(shuttle_id),
                str(shuttle_state),
                str(cur_dst),
                str(cur_node),
                str(cur_path),
                str(cur_psgr),
                str(cur_psgr_num)
            )
            
            insert_query = f"INSERT INTO {self.vehicle_table_name} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, values)
            self.connection.commit()

        except Exception as e:
            print(f"Error occurred in vehicle_data: {e}")
            if self.connection:
                self.connection.rollback()  # <--- ROLLBACK 추가

    def __del__(self):
        self.disconnect()
