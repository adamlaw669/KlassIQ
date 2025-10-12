#!/usr/bin/env python3
"""
Startup script for KlassIQ backend.
This script handles the deployment startup process.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """Main startup function."""
    try:
        # Import the FastAPI app
        from main import app
        
        # If running directly, start with uvicorn
        if __name__ == "__main__":
            import uvicorn
            port = int(os.environ.get("PORT", 8000))
            uvicorn.run(app, host="0.0.0.0", port=port)
        
        return app
        
    except ImportError as e:
        print(f"Error importing app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

# For deployment servers
app = main()

if __name__ == "__main__":
    main()