import pandas as pd
import numpy as np

target_df = pd.read_csv('SE-464-001 (1).csv')
grade_df = pd.read_csv('2025_SE464_Final_gradesheet.csv')

target_df['6'] = target_df['1'].map(
    np.floor(grade_df.set_index('ID')['Course grade']).astype('Int64')
)

target_df.to_csv('SE-464-001 (2).csv', index=False)