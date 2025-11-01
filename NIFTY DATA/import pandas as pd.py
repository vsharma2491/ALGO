import pandas as pd

df = pd.read_parquet(r'C:\Users\vivek\Desktop\algo\NIFTY DATA\NIFTY50-INDEX.parquet')
print(df.head())
print(df.head())
print(df.info())
df.set_index('Date', inplace=True)
df.drop(columns=['index'], inplace=True)

