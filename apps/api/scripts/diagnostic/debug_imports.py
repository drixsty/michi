import os
import sys
from datetime import date

sys.path.append(os.path.join(os.getcwd(), "src"))

from modules.forecasting.algorithms.out_of_stock_correction import correct_out_of_stock
from modules.forecasting.algorithms.outlier_detection import detect_outliers
from modules.forecasting.algorithms.run_rate import calculate_run_rate_batch

df = pd.DataFrame({
    "product_id": ["A"]*10,
    "date": pd.date_range("2024-01-01", periods=10),
    "units_sold": [10.0]*10,
    "end_of_day_stock": [100]*10
})

print("Testing OOS...")
df = correct_out_of_stock(df)
print("OOS OK")

print("Testing Outliers...")
df = detect_outliers(df)
print("Outliers OK")

print("Testing Run Rate...")
df_run = calculate_run_rate_batch(df)
print("Run Rate OK")
