from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson.objectid import ObjectId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ แก้ไขส่วนนี้
MONGO_URI = "mongodb+srv://phawitboo:tWtLjzg3r2RYmtty@cluster0.ljj8oii.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=False,
)

db = client["users"]
collection = db["profile"]

class UserUpdateModel(BaseModel):
    line_id: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    time_dca: Optional[str] = None

@app.post("/user/update_data")
def update_user(data: UserUpdateModel = Body(...)):
    result = collection.update_one(
        {"line_id": data.line_id},
        {"$set": data.dict(exclude_unset=True)},
        upsert=True
    )
    status = "updated" if result.matched_count else "created"
    return {"status": status, "line_id": data.line_id}

@app.get("/user/get_user_data/{line_id}")
def get_user(line_id: str):
    document = collection.find_one({"line_id": line_id})
    if document:
        document["_id"] = str(document["_id"])
        return document
    return {"error": "User not found"}
