#!/usr/bin/env python3
"""
🔬 SIMPLE API TEST
Minimal FastAPI server to test if the basic HTTP handling works
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Simple Test API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test")
async def test():
    return {"test": "working", "server": "simple"}

if __name__ == "__main__":
    print("🚀 Starting simple test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")