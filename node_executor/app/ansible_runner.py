import subprocess
from pathlib import Path

################
## CONSTANTES ##
################

# Directorio raíz del repo ansible-setup
ANSIBLE_PROJECT_DIR = Path(__file__).resolve().parents[2]

# Playbooks permitidos
ALLOWED_OPERATIONS = {
    "configure_nodes": "playbooks/kubernetes-nodes.yaml",
    "configure_control_plane": "playbooks/kubernetes-control-plane.yaml",
}


###############
## FUNCIONES ##
###############

def run_playbook(operation: str) -> dict:
    """
    Ejecuta un playbook de Ansible en función de la operación seleccionada
    """

    playbook = ALLOWED_OPERATIONS.get(operation)
    # Si no existe la operación, termina el proceso
    if playbook is None:
        return {"success": False, "error": f"Operación no permitida: {operation}"}
    
    command = ["ansible-playbook", playbook, "--check", "--diff"]

    try:
        result = subprocess.run(
            command,
            cwd=ANSIBLE_PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=3600
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "operation": operation,
            "playbook": playbook,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "La ejecución ha superado el tiempo máximo permitido"
        }
    except OSError as error:
        return {
            "success": False,
            "error": str(error)
        }
