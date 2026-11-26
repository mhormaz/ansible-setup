import subprocess
from pathlib import Path


# Directorio raíz del repositorio Ansible
ANSIBLE_PROJECT_DIR = Path("/home/control-plane1/ansible-setup")


def run_playbook(playbook: str) -> dict:
    """
    Ejecuta un playbook de Ansible desde el directorio del proyecto.
    """

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
