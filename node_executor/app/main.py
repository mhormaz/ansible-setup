from fastapi import FastAPI

app = FastAPI(
    title="Node Executor",
    description="Servicio de ejecución de operaciones Ansible",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {
        "service": "Node Executor",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }