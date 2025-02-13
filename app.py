from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import requests
import subprocess
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "script_runner",
            "description": "Install a package and run a script from a URL with provided arguments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_url": {
                        "type": "string",
                        "description": "The URL of the script to run."
                    },
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of arguments to pass to the script"
                    }
                },
                "required": ["script_url", "args"]
            }
        }
    }
]

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

@app.get("/")
def home():
    return {"message": "Yay TDS Tuesday is awesome."}

@app.get("/read")
def read_file(path: str):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=404, detail="File doesn't exist")

@app.post("/run")
def task_runner(task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": task},
            {
                "role": "system",
                "content": """
You are an assistant who has to do a variety of tasks.
- If your task involves running a script, you can use the `script_runner` tool.
- If your task involves writing code, you can use the `task_runner` tool.
"""
            }
        ],
        "tools": tools,
        "tools_choice": "auto"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()

        # Debugging: Print full AI API response
        logging.info("Full AI API Response: %s", json.dumps(response_json, indent=4))

        # Check if "choices" exists in response
        if "choices" not in response_json or not response_json["choices"]:
            raise HTTPException(status_code=500, detail=f"Invalid AI response format: {response_json}")

        tool_calls = response_json["choices"][0].get("message", {}).get("tool_calls", [])
        if not tool_calls:
            raise HTTPException(status_code=500, detail=f"No tool call found: {response_json}")

        # Extract tool arguments
        arguments = tool_calls[0]["function"].get("arguments", {})
        script_url = arguments.get("script_url")
        args = arguments.get("args", [])

        if not script_url or not args:
            raise HTTPException(status_code=400, detail=f"Invalid script execution request: {response_json}")

        email = args[0]
        command = ["uv", "run", script_url, email]

        logging.info(f"Running script: {script_url} with args {args}")
        subprocess.run(command, check=True)

        return {"message": f"Script {script_url} executed successfully with args {args}"}

    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to AI API: {e}")
        raise HTTPException(status_code=500, detail="AI API request failed")
    except subprocess.CalledProcessError as e:
        logging.error(f"Script execution failed: {e}")
        raise HTTPException(status_code=500, detail="Script execution error")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


