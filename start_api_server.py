#!/usr/bin/env python
"""Startup script for API server."""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Start the API server."""
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting LLM Family Doctor API Server...")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the API server
        subprocess.run([
            sys.executable, "api_server.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 API server stopped.")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 