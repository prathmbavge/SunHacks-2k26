import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

app = FastAPI(
    title=os.getenv("PROJECT_NAME", "Predictive Engineering Intelligence Platform"),
    description="PEIP Backend API"
)

@app.get("/health")
def health_check():
    """Health check route to ensure the server is running."""
    return {"status": "ok"}
