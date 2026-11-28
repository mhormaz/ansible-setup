from fastapi import FastAPI, HTTPException
from node_executor.app.ansible_runner import run_playbook, get_inventory_hosts

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
    return get_inventory_hosts()

@app.post("/operations/{operation}")
async def execute_operation(operation: str, limit: str | None = None):
    result = run_playbook(operation, limit)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)

    return result