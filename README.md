# ansible-setup
Todo lo necesario para montar Ansible en el nodo maestro y que pueda aprovisionar al resto de nodos worker que entren en el cluster.

Para preparar un nodo para el control plane ejecuta el script:

```sh
curl -H "Cache-Control: no-cache, no-store" -H "Pragma: no-cache" "https://raw.githubusercontent.com/mhormaz/ansible-setup/refs/heads/main/_node-scripts/prepareAnsibleNode.sh" | sudo bash
```

Para preparar un nodo worker, ejecuta el siguiente script:

```sh
curl -H "Cache-Control: no-cache, no-store" -H "Pragma: no-cache" "https://raw.githubusercontent.com/mhormaz/ansible-setup/refs/heads/main/_node-scripts/prepareBasicNode.sh" | sudo bash
```