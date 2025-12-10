# cisco_generator.py

"""
Generador de configuración Cisco IOS a partir de resultados VLSM.

Cada subred se asigna a una interfaz consecutiva:
GigabitEthernet0/0
GigabitEthernet0/1
GigabitEthernet0/2
...

El prefijo de interfaz puede modificarse desde gui.py
"""

def generate_cisco_config(vlsm_results, interface_prefix="GigabitEthernet0/"):
    """
    Recibe la lista de subredes generadas por calculate_vlsm()
    y construye la configuración Cisco IOS correspondiente.

    vlsm_results: lista de diccionarios con información de cada subred.
    interface_prefix: prefijo base de las interfaces (por ejemplo: "GigabitEthernet0/")
    """

    # Lista donde se guardarán todas las líneas del archivo final de configuración
    lines = []

    # Encabezado estético estilo Cisco
    lines.append("! =======================================")
    lines.append("! CONFIGURACIÓN GENERADA POR COMPILADOR VLSM")
    lines.append("! Compatible con Cisco IOS")
    lines.append("! =======================================\n")

    # Recorremos todas las subredes generadas por el VLSM
    for i, subnet in enumerate(vlsm_results):

        # Construcción del nombre de interfaz usando el índice
        # Ejemplo: GigabitEthernet0/0, GigabitEthernet0/1...
        iface = f"{interface_prefix}{i}"

        # Extraemos la IP de red asignada a la subred
        ip = subnet["direccionamiento_de_red"]

        # Máscara en formato decimal (255.255.255.x)
        mask = subnet["mascara_decimal"]

        # Nombre amigable de la subred.
        # Si no existe, se genera uno automáticamente.
        name = subnet.get("nombre_red") or f"SUBRED_{i}"

        # Comentarios informativos que acompañan a cada bloque de configuración
        lines.append(f"! -------------------------------")
        lines.append(f"! Subred: {name}")
        lines.append(f"! Hosts solicitados: {subnet['hosts_solicitados']}")
        lines.append(f"! Hosts disponibles: {subnet['hosts_encontrados']}")
        lines.append(f"! -------------------------------")

        # Entramos a la configuración de la interfaz correspondiente
        lines.append(f"interface {iface}")

        # Se asigna la descripción con el nombre de la subred
        lines.append(f" description {name}")

        # Asignación de la IP y la máscara en Cisco IOS
        lines.append(f" ip address {ip} {mask}")

        # Habilitar la interfaz (si está apagada)
        lines.append(" no shutdown")

        # Salimos del modo configuración de interfaz
        lines.append(" exit\n")

    # Sección final del archivo
    lines.append("! FIN DE CONFIGURACIÓN")

    # Convertimos la lista en un string separado por saltos de línea
    return "\n".join(lines)