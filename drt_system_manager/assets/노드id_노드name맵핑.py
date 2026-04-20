## 여기서 바로 실행 불가 ,colab 사용하기 

import pandas as pd
from IPython.display import FileLink

# 1) CSV 파일 읽기 (인코딩과 경로는 환경에 맞게 조정하세요)
df_bind = pd.read_csv('assets/위도경도_바인딩.csv', encoding='cp949')
df_cor  = pd.read_csv('assets/cor_node.csv',       encoding='utf-8')

# 2) 컬럼 이름 통일: '경도'→x, '위도'→y
df_bind = df_bind.rename(columns={'경도':'x', '위도':'y'})

# 3) x,y 좌표를 기준으로 두 DataFrame 병합
merged = pd.merge(
    df_bind[['id','x','y']],
    df_cor[['NODE_NAME','x','y']],
    on=['x','y'],
    how='inner'
)

# 4) 매핑 테이블(mapping_df) 추출
mapping_df = merged[['id','NODE_NAME']]

# 5) Python 딕셔너리 생성: { id: NODE_NAME, … }
node_dict = mapping_df.set_index('id')['NODE_NAME'].to_dict()

# 6) CSV로 저장
mapping_df.to_csv('/assets/mapping.csv', index=False, encoding='utf-8-sig')

# 7) 다운로드 링크 표시
FileLink('/assets/mapping.csv')




