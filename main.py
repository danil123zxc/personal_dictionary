#!/usr/bin/env python3
"""
Main application entry point.

This file serves as the entry point for the Personal Dictionary application.
It imports the FastAPI app from the reorganized source structure.
"""

import uvicorn
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
