from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import time
import hmac
import hashlib
import requests

app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === CSV file path ===
CSV_FILE = "user_profiles.csv"

# Create file if not exists
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["line_id", "api_key", "api_secret", "dca_amount", "time_dca"])
    df.to_csv(CSV_FILE, index=False)

# === Models ===
class UserUpdateModel(BaseModel):
    line_id: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    dca_amount: Optional[float] = None
    time_dca: Optional[str] = None  # <-- New field

# === Root ===
@app.get("/")
def root():
    return {"message": "🚀 FastAPI Bitkub DCA server is running."}

# === Update user ===
@app.post("/user/update_data")
def update_user(data: UserUpdateModel = Body(...)):
    df = pd.read_csv(CSV_FILE)
    existing_idx = df.index[df['line_id'] == data.line_id].tolist()
    new_row = data.dict()

    if existing_idx:
        for key, value in new_row.items():
            if value is not None:
                df.at[existing_idx[0], key] = value
        status = "updated"
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        status = "created"

    df.to_csv(CSV_FILE, index=False)
    return {"status": status, "line_id": data.line_id}

# === Get user ===
@app.get("/user/get_user_data/{line_id}")
def get_user(line_id: str):
    df = pd.read_csv(CSV_FILE)
    row = df[df["line_id"] == line_id]
    if not row.empty:
        return row.to_dict(orient="records")[0]
    return {"error": "User not found"}

# === Bitkub server time ===
@app.get("/bitkub/servertime")
def get_servertime():
    try:
        response = requests.get("https://api.bitkub.com/api/v3/servertime")
        return {"server_time": int(response.text)}
    except Exception as e:
        return {"error": str(e)}

# === Bitkub order history ===
@app.get("/bitkub/order-history/{line_id}")
def get_order_history(line_id: str, sym: str = "btc_thb", p: int = 1, lmt: int = 100):
    df = pd.read_csv(CSV_FILE)
    row = df[df["line_id"] == line_id]

    if row.empty:
        return {"error": "line_id not found"}
    
    api_key = row["api_key"].values[0]
    api_secret = row["api_secret"].values[0]
    if pd.isna(api_key) or pd.isna(api_secret):
        return {"error": "API credentials missing"}

    endpoint = "/api/v3/market/my-order-history"
    base_url = "https://api.bitkub.com"
    url = f"{base_url}{endpoint}"

    timestamp = int(time.time() * 1000)
    query_string = f"sym={sym}&p={p}&lmt={lmt}"
    message = f"{timestamp}GET{endpoint}?{query_string}"
    sign = hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-BTK-APIKEY": api_key,
        "X-BTK-TIMESTAMP": str(timestamp),
        "X-BTK-SIGN": sign,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params={"sym": sym, "p": p, "lmt": lmt})
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# === Bitkub DCA Now ===
@app.post("/bitkub/dca_now/{line_id}")
def dca_now(line_id: str):
    df = pd.read_csv(CSV_FILE)
    row = df[df["line_id"] == line_id]

    if row.empty:
        return {"error": "line_id not found"}

    api_key = row["api_key"].values[0]
    api_secret = row["api_secret"].values[0]
    dca_amount = row["dca_amount"].values[0]

    if pd.isna(api_key) or pd.isna(api_secret) or pd.isna(dca_amount):
        return {"error": "Incomplete user info"}

    endpoint = "/api/v3/market/place-bid"
    base_url = "https://api.bitkub.com"
    url = base_url + endpoint

    # payload = {
    #     "sym": "btc_thb",
    #     "amt": dca_amount,
    #     "rat": 0,
    #     "typ": "market",
    #     "client_id": "dca"
    # }
    payload = {
        "sym": "btc_thb",
        "amt": float(dca_amount),
        "rat": 0,  # Market price
        "typ": "market",
        "client_id" : "dca"
    }

    print('payload',payload)


    # payload = {
    #     "sym": "btc_thb",
    #     "amt": thb_amount,
    #     "typ": "market",
    #     "client_id": "dca"
    # }


    payload_str = str(payload).replace("'", '"')
    timestamp = int(time.time() * 1000)
    message = f"{timestamp}POST{endpoint}{payload_str}"
    sign = hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-BTK-APIKEY": api_key,
        "X-BTK-TIMESTAMP": str(timestamp),
        "X-BTK-SIGN": sign,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}



from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

# === DCA Loop สำหรับผู้ใช้ทั้งหมด ===
def run_scheduled_dca():
    print("⏰ Checking users for DCA...")

    try:
        df = pd.read_csv(CSV_FILE)
        tz = pytz.timezone("Asia/Bangkok")
        now_str = datetime.now(tz).strftime("%H:%M")

        for index, row in df.iterrows():
            user_time = str(row.get("time_dca", "")).strip()
            if user_time == now_str:
                print(f"🚀 Trigger DCA for {row['line_id']} at {user_time}")
                try:
                    dca_now(row["line_id"])
                except Exception as e:
                    print(f"❌ Failed DCA for {row['line_id']}: {e}")
    except Exception as e:
        print("Scheduler Error:", e)

# === เริ่ม Scheduler ทุก 60 วินาที ===
scheduler = BackgroundScheduler()
scheduler.add_job(run_scheduled_dca, 'interval', seconds=60)
scheduler.start()

