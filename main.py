from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
import os
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# MongoDB
client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
db = client.booksdb
books_col = db.books
music_col = db.music

# Hugging Face
HF_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

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
    return {"message": "🚀 Books-Music-AI + MongoDB + HF Live!"}

@app.post("/books")
async def add_book(book: Book):
    await books_col.insert_one(book.dict())
    return book

@app.get("/books")
async def get_books():
    books = await books_col.find().to_list(100)
    return books

@app.post("/music")
async def add_music(music: Music):
    await music_col.insert_one(music.dict())
    return music

@app.get("/music")
async def get_music():
    music = await music_col.find().to_list(100)
    return music

@app.post("/ai/image")
async def generate_image(prompt: str):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}
    response = requests.post(HF_URL, headers=headers, json=payload)
    return {"image_b64": str(response.content), "prompt": prompt}

@app.get("/health")
async def health():
    return {"status": "healthy"}
