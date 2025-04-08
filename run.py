import os
import subprocess
import time
import venv
from pathlib import Path
import webbrowser

VENV_DIR = Path("venv")
REQUIREMENTS_FILE = "requirements.txt"

def create_virtualenv():
    """Create a virtual environment if it doesn't exist."""
    print("🔧 Creating virtual environment...")
    venv.EnvBuilder(with_pip=True).create(VENV_DIR)

def get_venv_python():
    """Return the path to the Python interpreter inside the venv."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def install_requirements(python_path):
    """Install dependencies using the venv's Python."""
    print("📦 Installing dependencies from requirements.txt...")
    subprocess.check_call([str(python_path), "-m", "pip", "install", "-r", REQUIREMENTS_FILE])

def start_flask(python_path):
    """Start the Flask server using the venv's Python."""
    print("🚀 Starting Flask server...")
    return subprocess.Popen([str(python_path), "backend/app.py"])

def open_browser():
    """Open the landing page (index.html) in the default web browser."""
    print("🌐 Opening landing page...")
    # Change the URL to "/" so that it serves your index.html landing page
    webbrowser.open("http://127.0.0.1:5000/")

def run():
    """Main function to execute setup and run the application."""
    try:
        if not VENV_DIR.exists():
            create_virtualenv()

        venv_python = get_venv_python()
        install_requirements(venv_python)
        flask_process = start_flask(venv_python)
        time.sleep(5)  # Give Flask time to start up
        open_browser()
        flask_process.wait()
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    run()