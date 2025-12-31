from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

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
    return {"message": "🚀 Books-Music-AI Backend Live!"}

@app.post("/books")
async def add_book(book: Book):
    books.append(book)
    return {"added": book}

@app.get("/books")
async def get_books():
    return books

@app.post("/music")
async def add_music(music: Music):
    music.append(music)
    return {"added": music}

@app.get("/music")
async def get_music():
    return music

@app.post("/ai/image")
async def generate_image(prompt: str):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return {"image": response.content, "prompt": prompt}

@app.get("/health")
async def health():
    return {"status": "healthy"}
