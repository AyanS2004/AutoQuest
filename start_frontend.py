#!/usr/bin/env python3
"""
Start the AutoQuest frontend development server
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🎨 Starting AutoQuest Frontend...")
    print("=" * 50)
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return 1
    
    try:
        print("📦 Checking frontend dependencies...")
        
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        print("✅ Frontend dependencies ready")
        print()
        print("🚀 Starting development server...")
        print("📱 The frontend will be available at: http://localhost:5173")
        print("🌙 Dark mode is enabled by default")
        print("💡 You can toggle between light/dark mode using the theme button in the top bar")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the development server
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
        
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
        return 0
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
