import os
import pandas as pd

def calculate_and_save_sum_in_subfolders(root_folder):
    for root, dirs, files in os.walk(root_folder):
        End_total_sum = 0
        has_csv_files = False
        for file in files:
            total_sum = 0
            if file.endswith(".csv"):
                has_csv_files = True
                file_path = os.path.join(root, file)
                # 인코딩을 cp949로 설정하여 CSV 파일을 읽음
                try:
                    df = pd.read_csv(file_path, encoding='cp949')
                except UnicodeDecodeError:
                    print(f"Could not read file {file_path} with encoding 'cp949'. Trying 'utf-8'.")
                    df = pd.read_csv(file_path, encoding='utf-8')
                
                # 'G' 열 이후의 모든 열을 선택하여 합계를 계산
                total_sum = df.iloc[0:, 6:].sum().sum()
                if total_sum < 10:
                    print(df)
                End_total_sum = End_total_sum + total_sum
                
        if has_csv_files:
            # 각 하위 폴더 내에 결과를 텍스트 파일로 저장
            summary_path = os.path.join(root, "summary.txt")
            with open(summary_path, "w") as f:
                f.write(f"{End_total_sum}")

# "정류장별 이용량" 폴더의 경로를 지정
root_folder = os.getcwd()
calculate_and_save_sum_in_subfolders(root_folder)