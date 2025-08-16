"""
Root-level main.py for Render.com deployment
This avoids module path issues by providing the app at the root level
"""

from app.main import app

# Re-export the app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)
