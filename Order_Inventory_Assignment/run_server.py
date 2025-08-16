#!/usr/bin/env python3
"""
Universal Render.com deployment script
This script will work regardless of how Render.com detects the module path
"""

import os
import sys
from pathlib import Path

def setup_python_path():
    """Add all necessary paths to sys.path"""
    current_dir = Path(__file__).parent.absolute()
    
    # Add current directory
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Add app directory
    app_dir = current_dir / "app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    
    print(f"✅ Python path setup complete")
    print(f"   Current dir: {current_dir}")
    print(f"   App dir: {app_dir}")
    print(f"   Python path: {sys.path[:3]}...")

def main():
    """Main entry point"""
    setup_python_path()
    
    # Import uvicorn and the app
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import uvicorn: {e}")
        sys.exit(1)
    
    try:
        from app.main import app
        print("✅ FastAPI app imported successfully")
        print(f"   App title: {app.title}")
        print(f"   App version: {app.version}")
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        sys.exit(1)
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8007))
    host = "0.0.0.0"
    
    print(f"🚀 Starting server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
