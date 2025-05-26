import time
from ict_engine import run_ict_engine

print("🔁 ICT Bot is running. Checking for setups every 60 seconds...")

while True:
    try:
        run_ict_engine()
    except Exception as e:
        print("Error during execution:", e)
    time.sleep(60)