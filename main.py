from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Book(BaseModel):
    title: str
    author: str
    genre: str

class Music(BaseModel):
    title: str
    artist: str
    genre: str

books = []
music = []

@app.get("/")
async def root():
    return {"message": "✅ Backend ALIVE - CORS OK!"}

@app.get("/books")
async def get_books():
    return books

@app.post("/books")
async def add_book(book: Book):
    books.append(book.dict())
    return {"added": book.dict()}

@app.get("/music")
async def get_music():
    return music

@app.post("/music")
async def add_music(music: Music):
    music.append(music.dict())
    return {"added": music.dict()}

@app.post("/ai/image")
async def generate_image(prompt: str):
    return {"fake_image": f"Generated: {prompt}", "status": "ok"}

# RAILWAY PORT FIX
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
