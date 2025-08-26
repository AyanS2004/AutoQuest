#!/usr/bin/env python3
"""
AutoQuest GCC Web Interface Startup Script
Launches both backend and frontend servers
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🚀 AutoQuest GCC Web Interface")
    print("=" * 60)
    print("Starting backend and frontend servers...")
    print()

def check_dependencies():
    """Check if required files and dependencies exist"""
    print("🔍 Checking dependencies...")
    
    # Check required files
    required_files = ["solutions.xlsx", "template.xlsx"]
    for file in required_files:
        if not Path(file).exists():
            print(f"⚠️  Warning: {file} not found")
        else:
            print(f"✅ {file} found")
    
    # Check if frontend exists
    if not Path("frontend").exists():
        print("❌ Frontend directory not found")
        return False
    
    print("✅ Dependencies check complete")
    return True

def start_backend():
    """Start the backend server"""
    print("🔧 Starting backend server...")
    try:
        # Test if backend can start
        result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.append('.'); from autoquest.gcc import FinalPerfectGCCExtractor; print('Backend ready')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Backend dependencies OK")
            print("💡 To start backend manually: python run.py")
            return True
        else:
            print(f"❌ Backend test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Backend test error: {e}")
        return False

def start_frontend():
    """Start the frontend server"""
    print("🎨 Starting frontend server...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    try:
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        print("✅ Frontend dependencies OK")
        print("💡 To start frontend manually: cd frontend && npm run dev")
        return True
    except Exception as e:
        print(f"❌ Frontend setup error: {e}")
        return False

def print_instructions():
    """Print usage instructions"""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("📋 Next Steps:")
    print()
    print("1. 🖥️  Start Chrome with remote debugging:")
    print("   Windows: \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222")
    print("   macOS: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("   Linux: google-chrome --remote-debugging-port=9222")
    print()
    print("2. 🔧 Start the backend server:")
    print("   python run.py")
    print()
    print("3. 🎨 Start the frontend server:")
    print("   cd frontend && npm run dev")
    print("   Or use: python start_frontend.py")
    print()
    print("4. 🌐 Access the web interface:")
    print("   http://localhost:5173")
    print("   Then click on '☁️ GCC Extraction' or go to /gcc")
    print("   🌙 Dark mode is enabled by default")
    print()
    print("5. 🧪 Test the system:")
    print("   python test_gcc_simple.py")
    print()
    print("📚 For detailed instructions, see: README-GCC-INTEGRATION.md")
    print("=" * 60)

def main():
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        return 1
    
    print()
    
    # Test backend
    if not start_backend():
        print("\n❌ Backend test failed. Please check the errors above.")
        return 1
    
    print()
    
    # Test frontend
    if not start_frontend():
        print("\n❌ Frontend test failed. Please check the errors above.")
        return 1
    
    print_instructions()
    return 0

if __name__ == "__main__":
    sys.exit(main())
