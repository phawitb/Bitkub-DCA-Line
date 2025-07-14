from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson.objectid import ObjectId
import ssl

app = FastAPI()

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MongoDB Connection (TLS 1.2) ===
MONGO_URI = "mongodb+srv://phawitboo:tWtLjzg3r2RYmtty@cluster0.ljj8oii.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=False,
    ssl_cert_reqs=ssl.CERT_REQUIRED,
    ssl_version=ssl.PROTOCOL_TLSv1_2
)

db = client["users"]
collection = db["profile"]

# === Request Model ===
class UserUpdateModel(BaseModel):
    line_id: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    time_dca: Optional[str] = None

# === POST: Update or Create User ===
@app.post("/user/update_data")
def update_user(data: UserUpdateModel = Body(...)):
    result = collection.update_one(
        {"line_id": data.line_id},
        {"$set": data.dict(exclude_unset=True)},
        upsert=True
    )
    status = "updated" if result.matched_count else "created"
    return {"status": status, "line_id": data.line_id}

# === GET: Read User Data ===
@app.get("/user/get_user_data/{line_id}")
def get_user(line_id: str):
    document = collection.find_one({"line_id": line_id})
    if document:
        document["_id"] = str(document["_id"])  # ObjectId → str
        return document
    return {"error": "User not found"}
