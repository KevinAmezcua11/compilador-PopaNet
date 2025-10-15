# vlsm_calc.py
import math
import ipaddress

def calculate_vlsm(ip_address, subnet_mask, num_hosts_list, nombre_red=None):
    """
    Calcula las subredes resultantes aplicando VLSM.
    Retorna una lista de diccionarios con la información de cada subred.
    """
    results = []
    # Crea la red base a partir de la IP y la máscara
    base_network = ipaddress.IPv4Network(f"{ip_address}{subnet_mask}", strict=True)
    current_ip = int(base_network.network_address) 

    # Ordena las subredes de mayor a menor cantidad de hosts
    sorted_hosts = sorted(num_hosts_list, reverse=True)

    for num_hosts in sorted_hosts:
        # Calcula los bits necesarios para los hosts y la nueva máscara
        bits_host = math.ceil(math.log2(num_hosts + 2))  # +2 por red y broadcast
        new_cidr = 32 - bits_host
        block_size = 2 ** bits_host

        # Calcula direcciones de red, broadcast y rango utilizable
        network_address = ipaddress.IPv4Address(current_ip)
        broadcast_address = ipaddress.IPv4Address(current_ip + block_size - 1)
        first_usable_ip = ipaddress.IPv4Address(current_ip + 1)
        last_usable_ip = ipaddress.IPv4Address(current_ip + block_size - 2)
        decimal_mask = str(ipaddress.IPv4Network(f"0.0.0.0/{new_cidr}").netmask)

        # Agrega los resultados de la subred
        results.append({
            'hosts_solicitados': num_hosts,
            'hosts_encontrados': block_size - 2,
            'direccionamiento_de_red': str(network_address),
            'nueva_mascara': f"/{new_cidr}",
            'mascara_decimal': decimal_mask,
            'primera_ip_utilizable': str(first_usable_ip),
            'ultima_ip_utilizable': str(last_usable_ip),
            'direccion_de_broadcast': str(broadcast_address),
            'ip_base': ip_address,
            'nombre_red': nombre_red
        })

        # Avanza al siguiente bloque de direcciones
        current_ip += block_size

    return results
