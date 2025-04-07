import os
import sys
import subprocess
import time
import webbrowser

def install_requirements():
    """Install dependencies from requirements.txt."""
    print("Installing dependencies from requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_flask():
    """Start the Flask server."""
    print("Starting Flask server...")
    flask_process = subprocess.Popen([sys.executable, "backend/app.py"])
    time.sleep(5)  # Give Flask time to start up
    return flask_process

def open_browser():
    """Open the login page in the default web browser."""
    print("Opening login page...")
    webbrowser.open("http://127.0.0.1:5000/login")

def run():
    """Main function to execute the setup and run the application."""
    try:
        install_requirements()  # Install dependencies
        flask_process = start_flask()  # Start the Flask server
        open_browser()  # Open the login page in the browser
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # You can optionally wait for the Flask process to finish
        flask_process.wait()

if __name__ == "__main__":
    run()
