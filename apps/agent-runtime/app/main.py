# pyright: reportMissingImports=false

from fastapi import FastAPI

app = FastAPI()

app = FastAPI(
    title="Multiagent Negotiation Layer",
    description="agent runtime form mnl -v2",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return{
        "status": "ok",
        "service":"mnl agent-runtime",
        "version":"0.1.0",
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to MNL Agent Runtime"
    }