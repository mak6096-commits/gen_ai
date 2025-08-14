#!/usr/bin/env python3
import subprocess
import sys

def start_server(port=8002):
    """Start the FastAPI server"""
    try:
        print(f"Starting FastAPI server on port {port}...")
        subprocess.run([
            'python3', '-m', 'uvicorn', 
            'assignment_1:app', 
            '--port', str(port), 
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    port = 8002
    print("Starting Assignment 1 - Multiplication API")
    start_server(port)
