import subprocess
import json
from pathlib import Path

################
## CONSTANTES ##
################

# Directorio raíz del repo ansible-setup (subir dos niveles de la carpeta de ejecución del executor)
ANSIBLE_PROJECT_DIR = Path(__file__).resolve().parents[2]

# Playbooks permitidos
ALLOWED_OPERATIONS = {
    # Este playbook, sirve para preparar un nodo, que es lo todo lo que necesita un worker, pero puede usarse en un control plane, 
    # y luego usar el playbook dedicado, que sería lo mismo que usarlo directamente ya que ambos comparten la misma tarea inicial.
    "configure_worker": "playbooks/kubernetes-nodes.yaml",
    "configure_control_plane": "playbooks/kubernetes-control-plane.yaml",
}

INVENTORY_FILE = ANSIBLE_PROJECT_DIR / "inventory/hosts.yaml"

###############
## FUNCIONES ##
###############


def get_inventory_hosts() -> list[str]:
    """
    Obtiene los nombres de los hosts definidos en el inventario.
    """

    # Recuperamos el inventario actual
    result = subprocess.run(
        # No es necesario especificar el inventario
        ["ansible-inventory", "-i", str(INVENTORY_FILE), "--list"],
        cwd=ANSIBLE_PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True
    )

    # Lo cargamos usando la biblioteca json (es el formato del inventario que devuelve el comando anterior)
    inventory = json.loads(result.stdout)

    # Guardamos dentro de un set los hosts
    hosts = set()
    for group in inventory.values():
        if isinstance(group, dict):
            hosts.update(group.get("hosts", []))

    return sorted(hosts)

def run_playbook(operation: str, limit:str | None = None) -> dict:
    """
    Ejecuta un playbook de Ansible en función de la operación seleccionada.
    Se permite la ejecución de la operación en máquinas concretas (limit)
    """

    # Resolvemos la operación y creamos el comando a ejecutar
    playbook = ALLOWED_OPERATIONS.get(operation)
    if playbook is None:
        return {"success": False, "error": f"Operación no permitida: {operation}"}
    command = ["ansible-playbook", playbook, "--check", "--diff"]

    # Si se ha seleccionado una serie de máquinas a las que aplicar el comando, se extiende con "--limit".
    if limit:
        #Buscamos todos los host
        try:
            available_hosts = get_inventory_hosts()
        except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
            return {
                "success": False,
                "error": f"No se pudo consultar el inventario: {error}"
            }

        # Creamos el array de hosts (o host) afectados por "limit"
        requested_hosts = [host.strip() for host in limit.split(",")]
        if not requested_hosts or any(not host for host in requested_hosts):
            return {
                "success": False,
                "error": "La selección de nodos no es válida"
            }

        # Comprobamos que los host seleccionados sean válidos (estén en el inventario)
        invalid_hosts = [host for host in requested_hosts if host not in available_hosts]
        if invalid_hosts:
            return {
                "success": False,
                "error": f"Nodos no encontrados en el inventario: {invalid_hosts}"
            }

        # Añadimos al comando los hosts a los que se va a aplicar
        command.extend(["--limit", ",".join(requested_hosts)])    

    try:
        result = subprocess.run(
            command,
            cwd=ANSIBLE_PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=900 #15 minutos de timeout
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
