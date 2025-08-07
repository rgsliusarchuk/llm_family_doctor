#!/usr/bin/env python
"""Startup script for Streamlit app."""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Start the Streamlit app."""
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting LLM Family Doctor Streamlit App...")
    print("📱 Streamlit will be available at: http://localhost:8501")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped.")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 