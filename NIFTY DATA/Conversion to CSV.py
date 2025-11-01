import pandas as pd

df = pd.read_parquet(r'c:/Users/vivek/Desktop/algo/NIFTY DATA/NIFTY50-INDEX.parquet')
df.to_csv(r'c:/Users/vivek/Desktop/algo/NIFTY DATA/NIFTY50-INDEX.csv', index=False)
print("Conversion to CSV completed!")
