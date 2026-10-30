import os
import time
import urllib.request

SERVICE_URL = os.environ.get("INVENTORY_URL", "http://inventory:8080/inventory")

while True:
    try:
        with urllib.request.urlopen(SERVICE_URL, timeout=3) as response:
            print(f"status={response.status} response={response.read().decode()}", flush=True)
    except Exception as error:
        print(f"request failed: {error}", flush=True)
    time.sleep(2)
