"""Minimal demo wiring of the INJ credit economy.

    pip install -r requirements.txt          # needs Python 3.12
    INJ_TREASURY_ADDRESS=inj1... uvicorn server.app:app --port 8000

Then drive it with the X-Login-Address header (your wallet address):
    curl -H 'X-Login-Address: 0xyou' http://127.0.0.1:8000/api/points
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .points_routes import api

app = FastAPI(title="Maneki Inj — INJ credit economy")
app.include_router(api)
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"), html=True), name="web")
