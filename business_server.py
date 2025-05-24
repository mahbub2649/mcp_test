from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import requests

app = FastAPI()

# Dummy data stores
agents = {}
tasks = {
    "task1": {"description": "Update inventory", "priority": "high"},
    "task2": {"description": "Sync logs", "priority": "medium"},
}

# Models
class AgentRegistration(BaseModel):
    name: str
    version: str

class StatusReport(BaseModel):
    agent_id: str
    status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None

class NumberInput(BaseModel):
    number: int

# Endpoints
@app.post("/register")
def register_agent(agent: AgentRegistration):
    agent_id = str(uuid4())
    agents[agent_id] = {"name": agent.name, "version": agent.version}
    return {"agent_id": agent_id}

@app.post("/report_status")
def report_status(report: StatusReport):
    if report.agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": f"Status received for agent {report.agent_id}"}

@app.get("/tasks")
def get_tasks(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"tasks": tasks}

@app.post("/adder")
def adder(input: NumberInput):
    return {"result": input.number + 1}

@app.get("/joke")
def get_joke():
    try:
        response = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "setup": data.get("setup"),
            "punchline": data.get("punchline")
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail="Could not fetch joke")
