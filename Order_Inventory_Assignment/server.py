#!/usr/bin/env python3
"""
Render.com compatible server module
Exports 'app' for uvicorn to find
"""

import os
import sys
from pathlib import Path

# Setup Python path
current_dir = Path(__file__).parent.absolute()
app_dir = current_dir / "app"

# Add paths to sys.path
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Import the FastAPI app
try:
    from app.main import app
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    print(f"Current directory: {current_dir}")
    print(f"App directory: {app_dir}")
    print(f"Python path: {sys.path[:5]}")
    raise

# This is what uvicorn will look for
__all__ = ["app"]
