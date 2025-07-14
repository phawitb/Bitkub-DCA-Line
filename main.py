from fastapi import FastAPI, Body
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URI = "mongodb+srv://phawitboo:tWtLjzg3r2RYmtty@cluster0.ljj8oii.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URI)

# ✅ Use correct database and collection
db = client["users"]
collection = db["profile"]

# Request Model
class UserUpdateModel(BaseModel):
    line_id: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    time_dca: Optional[str] = None

@app.post("/user/update_data")
async def update_user(data: UserUpdateModel = Body(...)):
    result = await collection.update_one(
        {"line_id": data.line_id},
        {"$set": data.dict(exclude_unset=True)},
        upsert=True
    )
    
    status = "updated" if result.matched_count else "created"
    return {"status": status, "line_id": data.line_id}

@app.get("/user/get_user_data/{line_id}")
async def get_user(line_id: str):
    document = await collection.find_one({"line_id": line_id})
    if document:
        document["_id"] = str(document["_id"])  # Convert ObjectId to string for JSON
        return document
    return {"error": "User not found"}

