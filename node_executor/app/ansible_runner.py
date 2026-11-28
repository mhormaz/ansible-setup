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
    # Los playbooks solo se ejecutan si la máquina pertenece a ese grupo
    "configure_worker": {
        "playbook": "playbooks/kubernetes-nodes.yaml",
        "group": "workers"
    },
    "configure_control_plane": {
        "playbook": "playbooks/kubernetes-control-plane.yaml",
        "group": "control_planes"
    }
}

INVENTORY_FILE = ANSIBLE_PROJECT_DIR / "inventory/hosts.yaml"

###############
## FUNCIONES ##
###############

def get_inventory_group_hosts(group_name: str) -> list[str]:
    """
     Se encarga de devolver un listado con todas las máquinas de un grupo seleccionado.
    """

    result = subprocess.run(
        [
            "ansible-inventory",
            "-i", str(INVENTORY_FILE),
            "--list"
        ],
        cwd=ANSIBLE_PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True
    )

    # Devolvemos los hots del grupo seleccionado
    inventory = json.loads(result.stdout)
    group = inventory.get(group_name, {})
    return group.get("hosts", [])



def get_inventory_hosts() -> list[str]:
    """
    Se encarga de devolver un listado con todas las máquinas del inventario.
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
    Se permite la ejecución de la operación en máquinas concretas (limit).
    """

    # Resolvemos la operación y su grupo permitido
    operation_pair = ALLOWED_OPERATIONS.get(operation)
    if operation_pair is None:
        return {"success": False, "error": f"Operación no permitida: {operation}"}
    playbook = operation_pair["playbook"]
    allowed_group = operation_pair["group"]

    #Buscamos los hosts del grupo permitido
    try:
        available_hosts = get_inventory_group_hosts(allowed_group)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
        return {
            "success": False,
            "error": f"No se pudo consultar el inventario: {error}"
        }

    # Si se ha seleccionado una serie de máquinas a las que aplicar el comando, se comprueba si pertenecen al grupo permitido
    if limit:
        # Creamos el array de hosts (o host) afectados por "limit"
        requested_hosts = [host.strip() for host in limit.split(",")]
        if not requested_hosts or any(not host for host in requested_hosts):
            return {
                "success": False,
                "error": "La selección de nodos no es válida"
            }

        # Comprobamos que los host seleccionados sean válidos (pertenecen al grupo de la operación realizada)
        invalid_hosts = [host for host in requested_hosts if host not in available_hosts]
        if invalid_hosts:
            return {
                "success": False,
                "error": (f"Los siguientes nodos no pertenecen al grupo " 
                          f"'{allowed_group}': {invalid_hosts}")
            }
        
        # Creamos el listado de hosts (o host)
        selected_hosts = ",".join(requested_hosts)
    else:
        # Si no hay limit, se seleccionan todos los nodos de ese grupo
        selected_hosts = allowed_group


    command = ["ansible-playbook", playbook, "--limit", selected_hosts, "--check", "--diff"]
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
            "group": allowed_group,
            "limit": selected_hosts,
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
