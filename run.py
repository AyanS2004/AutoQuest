#!/usr/bin/env python3
"""
RAGbot Pro - Entry Point
Run this script to start the RAGbot application.
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="RAG-Enhanced Enterprise AI Platform")
    parser.add_argument(
        "--mode", 
        choices=["fastapi"], 
        default="fastapi",
        help="Application mode (FastAPI only)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to run on (default: 8000)"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["PORT"] = str(args.port)
    os.environ["HOST"] = args.host
    os.environ["DEBUG"] = str(args.debug).lower()
    
    # Check if .env file exists, if not create from example
    if not Path(".env").exists() and Path("env.example").exists():
        print("Creating .env file from env.example...")
        import shutil
        shutil.copy("env.example", ".env")
        print("Please edit .env file with your configuration before running again.")
        return
    
    # Determine which app to run (FastAPI only)
    if args.mode == "fastapi":
        run_fastapi_app(args)
    else:
        run_fastapi_app(args)

def run_fastapi_app(args):
    """Run the FastAPI application"""
    print("Starting RAGbot Pro with FastAPI...")
    
    # Check for required dependencies
    required_packages = ['fastapi', 'uvicorn', 'structlog', 'prometheus_client']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        raise ImportError(f"Missing packages: {missing_packages}")
    
    import uvicorn
    from main import app
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="debug" if args.debug else "info"
    )

def run_flask_app(args):
    raise RuntimeError("Flask mode has been removed. Use --mode fastapi")

if __name__ == "__main__":
    main() 