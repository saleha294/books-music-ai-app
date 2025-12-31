from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uvicorn
import shutil
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import Dict, Any, List

# Fix ObjectId serialization globally
def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(doc, dict):
        doc = doc.copy()
        if '_id' in doc:
            doc['id'] = str(doc['_id'])
            del doc['_id']
        return {k: serialize_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload folders
book_uploads = Path("book_uploads")
book_uploads.mkdir(exist_ok=True)
music_uploads = Path("music_uploads")
music_uploads.mkdir(exist_ok=True)

# Serve uploaded files publicly
app.mount("/books/files", StaticFiles(directory="book_uploads"), name="book_files")
app.mount("/music/files", StaticFiles(directory="music_uploads"), name="music_files")

# Global DB client
client = None
db = None

@app.on_event("startup")
async def startup_db_client():
    global client, db
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            print("❌ MONGODB_URI environment variable not found")
            return
            
        client = AsyncIOMotorClient(mongo_uri)
        db = client["booksdb"]
        await db.command("ping")
        print(f"✅ Connected to MongoDB: booksdb")
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
    try:
        if db is None:
            return {"error": "Database not connected"}
        books = await db.books.find({}).to_list(100)
        return serialize_doc(books)
    except Exception as e:
        print(f"Books GET error: {e}")
        return {"error": "Failed to fetch books", "details": str(e)}

@app.post("/books")
async def add_book(book: Book):
    try:
        if db is None:
            return {"error": "Database not connected"}
        await db.books.insert_one(book.dict())
        return {"added": book.dict()}
    except Exception as e:
        print(f"Books POST error: {e}")
        return {"error": "Failed to add book", "details": str(e)}

# NEW: PDF Book Upload
@app.post("/books/upload")
async def upload_book(
    title: str = Form(...),
    author: str = Form(...),
    genre: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        if db is None:
            return {"error": "Database not connected"}
        
        # Validate PDF
        if not file.filename.lower().endswith('.pdf'):
            return {"error": "Only PDF files allowed"}
        
        # Save PDF file
        file_path = book_uploads / f"{title.replace(' ', '_')}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Save to database with file URL
        book_data = {
            "title": title,
            "author": author,
            "genre": genre,
            "file_url": f"/books/files/{file_path.name}",
            "file_size": file.size
        }
        await db.books.insert_one(book_data)
        return {"added": serialize_doc(book_data)}
    except Exception as e:
        print(f"Book upload error: {e}")
        return {"error": "Failed to upload book", "details": str(e)}

@app.get("/music")
async def get_music():
    try:
        if db is None:
            return {"error": "Database not connected"}
        music = await db.music.find({}).to_list(100)
        return serialize_doc(music)
    except Exception as e:
        print(f"Music GET error: {e}")
        return {"error": "Failed to fetch music", "details": str(e)}

@app.post("/music")
async def add_music(music_item: Music):
    try:
        if db is None:
            return {"error": "Database not connected"}
        await db.music.insert_one(music_item.dict())
        return {"added": music_item.dict()}
    except Exception as e:
        print(f"Music POST error: {e}")
        return {"error": "Failed to add music", "details": str(e)}

@app.post("/music/upload")
async def upload_music(
    title: str = Form(...),
    artist: str = Form(...),
    genre: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        if db is None:
            return {"error": "Database not connected"}
        
        # Validate audio
        if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a')):
            return {"error": "Only MP3, WAV, M4A files allowed"}
        
        # Save audio file
        file_path = music_uploads / f"{title.replace(' ', '_')}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Save to database with file URL
        music_data = {
            "title": title,
            "artist": artist,
            "genre": genre,
            "file_url": f"/music/files/{file_path.name}",
            "file_size": file.size
        }
        await db.music.insert_one(music_data)
        return {"added": serialize_doc(music_data)}
    except Exception as e:
        print(f"Music upload error: {e}")
        return {"error": "Failed to upload music", "details": str(e)}


# RAILWAY PORT FIX
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
