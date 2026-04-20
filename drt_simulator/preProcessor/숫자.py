import os
import pandas as pd

def save_summary_to_csv(root_folder, output_csv_path):
    # 결과를 저장할 리스트
    summary_data = []

    # root_folder 아래의 모든 폴더를 순회
    for root, dirs, files in os.walk(root_folder):
        text_number = None
        csv_count = 0
        for file in files:
            if file.endswith(".txt"):  # 텍스트 파일을 찾음
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    text_number = f.read().strip()  # 텍스트 파일에서 숫자를 읽음
            elif file.endswith(".csv"):  # CSV 파일의 개수를 세는 부분
                csv_count += 1

        # 폴더에 텍스트 파일이 있는 경우만 처리
        if text_number is not None:
            # 숫자를 csv 파일의 개수로 나누어 계산
            division_result = float(text_number) / csv_count if csv_count else 0
            # 폴더 이름, 숫자, csv 파일 개수, 나눈 결과를 리스트에 추가
            summary_data.append([os.path.basename(root), text_number, csv_count, division_result])

    # 결과를 DataFrame으로 변환
    df_summary = pd.DataFrame(summary_data, columns=['Folder Name', 'Number', 'CSV Count', 'Number per CSV'])

    # DataFrame을 CSV 파일로 저장
    df_summary.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

# 'root' 폴더 경로와 출력할 CSV 파일의 경로를 지정
root_folder = os.getcwd()
output_csv_path = os.path.join(root_folder, 'summary.csv')

save_summary_to_csv(root_folder, output_csv_path)