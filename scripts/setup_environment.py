#!/usr/bin/env python
"""
Environment setup script for the LLM Family Doctor project.

This script helps set up the environment for both local development
and Google Colab usage.

Usage:
    python scripts/setup_environment.py
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit', 'pdfplumber', 'tqdm', 'sentence-transformers',
        'faiss-cpu', 'numpy', 'pydantic-settings', 'python-dotenv',
        'langchain', 'langchain-openai', 'langsmith'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        return False
    
    print("\n✅ All required packages are installed")
    return True

def install_dependencies():
    """Install dependencies from requirements.txt."""
    print("🔄 Installing dependencies...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False

def setup_environment_variables():
    """Set up environment variables."""
    print("🔧 Setting up environment variables...")
    
    env_vars = {
        "MODEL_ID": "intfloat/multilingual-e5-base",
        "INDEX_PATH": "data/faiss_index",
        "MAP_PATH": "data/doc_map.pkl"
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    # Write to .env file
    env_content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
    Path(".env").write_text(env_content)
    print("✅ Environment variables written to .env file")
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "data/raw_pdfs",
        "data/protocols",
        "logs",
        "tests"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    return True

def check_data_files():
    """Check if data files exist."""
    print("📊 Checking data files...")
    
    files_to_check = [
        ("data/faiss_index", "FAISS index"),
        ("data/doc_map.pkl", "Document map"),
        ("data/protocols", "Protocols directory")
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        path = Path(file_path)
        if path.exists():
            if path.is_dir():
                files = list(path.glob("*"))
                print(f"   ✅ {description}: {len(files)} files")
            else:
                print(f"   ✅ {description}: exists")
        else:
            print(f"   ❌ {description}: not found")
            all_exist = False
    
    return all_exist

def detect_environment():
    """Detect if running in Colab or local environment."""
    try:
        import google.colab
        print("🌐 Detected: Google Colab environment")
        return "colab"
    except ImportError:
        print("💻 Detected: Local environment")
        return "local"

def main():
    """Main setup function."""
    print("🚀 LLM Family Doctor - Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Detect environment
    env_type = detect_environment()
    print()
    
    # Create directories
    if not create_directories():
        return False
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n🔄 Installing missing dependencies...")
        if not install_dependencies():
            return False
        print()
    
    # Setup environment variables
    if not setup_environment_variables():
        return False
    print()
    
    # Check data files
    data_exists = check_data_files()
    print()
    
    if data_exists:
        print("✅ Setup complete! All components are ready.")
        print("\n📋 Next steps:")
        print("   1. Add PDF files to data/raw_pdfs/")
        print("   2. Run the data preparation notebook")
        print("   3. Test the index with: python tests/test_index.py")
    else:
        print("⚠️  Setup complete, but data files are missing.")
        print("\n📋 Next steps:")
        print("   1. Add PDF files to data/raw_pdfs/")
        print("   2. Run: python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive")
        print("   3. Run: python src/indexing/build_index.py")
        print("   4. Test with: python tests/test_index.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 