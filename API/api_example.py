from fastapi import FastAPI
import uvicorn
from pyngrok import ngrok
import nest_asyncio
import os
import subprocess

app = FastAPI()

@app.get("/add")
def add(a: int, b: int):
    return {"result": a + b}

@app.delete("/delete")
def delete(a: int, b: int):
    return {"result": a - b}

async def main():
    ngrok.set_auth_token("312IWrBJtgacc2Z84AhbyzntgdY_544dv17iZEAP1VLB9UyCS")
    # Set up ngrok tunnel
    http_tunnel = ngrok.connect(8000)
    print(f"Public URL: {http_tunnel.public_url}")

    # Run the FastAPI app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def kill_process_on_port(port):
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        pid = result.stdout.strip()
        if pid:
            subprocess.run(['kill', '-9', pid])
            print(f"Killed process {pid} on port {port}")
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")

if __name__ == "__main__":
    kill_process_on_port(8000)
    nest_asyncio.apply()
    import asyncio
    asyncio.run(main())