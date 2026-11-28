import subprocess
import json
from fastapi import FastAPI, HTTPException
from node_executor.app.ansible_runner import run_playbook, get_inventory_nodes

app = FastAPI(
    title="Node Executor",
    description="Servicio de ejecución de operaciones Ansible",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"service": "Node Executor", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/nodes")
async def get_nodes():
    try:
        return get_inventory_nodes()
    except (subprocess.CalledProcessError, json.JSONDecodeError, RuntimeError) as error:
        raise HTTPException(status_code=500,detail=str(error))

# Las operaciones son: configure_worker, configure_control_plane
@app.post("/operations/{operation}")
async def execute_operation(operation: str, limit: str | None = None):
    result = run_playbook(operation, limit)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)
    return result