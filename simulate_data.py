import time
import pandas as pd
from pathlib import Path

# SETTINGS
SOURCE_CSV = "Table2_Shipping.csv"
TARGET_CSV = "live_shipping.csv"
INTERVAL_SECONDS = 5  # ⏱ Change to 60 for 1 minute intervals

# Load source rows
df = pd.read_csv(SOURCE_CSV)
rows = df.to_dict(orient="records")

# Create target file with header if it doesn't exist
target_path = Path(TARGET_CSV)
if not target_path.exists():
    pd.DataFrame(columns=df.columns).to_csv(TARGET_CSV, index=False)

# Start appending loop
print(f"🚚 Starting live simulation. Appending 1 row every {INTERVAL_SECONDS} seconds...")

for row in rows:
    row_df = pd.DataFrame([row])
    row_df.to_csv(TARGET_CSV, mode='a', header=False, index=False)
    print(f"✅ Appended: {row['shipment_id']} → {row['status']}")
    time.sleep(INTERVAL_SECONDS)

print("✅ All rows streamed.")
