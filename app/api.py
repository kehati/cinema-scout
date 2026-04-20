import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.brain import get_cinema_scout_agent

app = FastAPI(title="Cinema Scout Agent API")

# Initialize the agent once when the server starts
print("Loading Agent...")
agent_executor = get_cinema_scout_agent()


class ChatRequest(BaseModel):
    input: str


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        full_response = agent_executor.invoke({"input": request.input})
        output_text = full_response["output"]

        # Clean up LangChain raw output format
        if isinstance(output_text, list):
            clean_text = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in output_text
            )
        else:
            clean_text = str(output_text)

        return {"output": clean_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))