#!/usr/bin/env python3
"""
Render.com startup script for Orders & Inventory Microservice
This script handles the module path issues on Render.com
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    port = int(os.environ.get("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)
