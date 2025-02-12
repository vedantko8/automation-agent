from fastapi import FastAPI , HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

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
            "description": "Install a package and run a script from a url with provided arguments.",
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
        raise HTTPException(status_code=404, detail="File doesn't exits")
    
@app.post("/run")
def task_runner(task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"  # Removed parentheses around token
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": task
            },
            {
                "role": "system",
                "content": """
You are an assistant who has to do a variety of tasks
If your task involves running a script, you can use the script_runner tool.
If your task involves writing a code, you can use the task_runner tool."""

            }
        ],
        "tools": tools,
        "tools_choice": "auto"
    
    }
    response = requests.post(url=url, headers=headers, json=data)  # Use requests.post
    return response.json()["choices"][0]["message"]["tool_calls"][0]["function"]


    



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


