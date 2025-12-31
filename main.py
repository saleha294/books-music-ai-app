from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()  # MOVED UP - must exist before @app decorators

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global DB client
client = None
db = None

@app.on_event("startup")
async def startup_db_client():
    global client, db
    try:
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        db = client.booksdb
        # Test connection
        await db.command("ping")
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()

class Book(BaseModel):
    title: str
    author: str
    genre: str

class Music(BaseModel):
    title: str
    artist: str
    genre: str

@app.get("/")
async def root():
    return {"message": "✅ Backend ALIVE - CORS OK!"}

@app.get("/books")
async def get_books():
    if db is None:
        return {"error": "Database not connected"}
    books = await db.books.find({}).to_list(100)
    return books

@app.post("/books")
async def add_book(book: Book):
    if db is None:
        return {"error": "Database not connected"}
    await db.books.insert_one(book.dict())
    return {"added": book.dict()}

@app.get("/music")
async def get_music():
    if db is None:
        return {"error": "Database not connected"}
    music = await db.music.find({}).to_list(100)
    return music

@app.post("/music")
async def add_music(music_item: Music):
    if db is None:
        return {"error": "Database not connected"}
    await db.music.insert_one(music_item.dict())
    return {"added": music_item.dict()}

# RAILWAY PORT FIX
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
