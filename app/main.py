from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.modules.store import init_db
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.modules.ingestor import fetch_alerts

load_dotenv()

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(fetch_alerts, "interval", minutes=5)
    scheduler.start()
    print("[scheduler] polling Wazuh every 5 minutes")
    yield
    scheduler.shutdown()

app = FastAPI(
    title="WazuhAI",
    description="AI-powered anomaly detection on Wazuh alerts",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "project": "WazuhAI",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
def health():
    return {"status": "ok"}