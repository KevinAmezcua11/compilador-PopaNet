# semantic.py
import ipaddress
import math
from ir import IREmitter

class VLSMSemanticAnalyzer:
    def __init__(self, blocks):
        # Recibe los bloques sintácticos para analizar semánticamente
        self.blocks = blocks
        self.errors = []
        
    def analyze(self):
        """
        Analiza todos los bloques y acumula errores semánticos.
        """
        self.errors = []
        for block in self.blocks:
            self._validate_block(block)
        return not bool(self.errors)

    def _validate_block(self, block):
        """
        Realiza validaciones semánticas sobre un bloque:
        - IP válida
        - Máscara válida
        - Hosts positivos
        - Espacio suficiente para subredes
        """
        ip_addr_str = block['ip_address']
        cidr_str = block['subnet_mask']
        hosts_list = block['num_hosts']
        name = block.get('name', 'Bloque anónimo')
        
        try:
            ip = ipaddress.IPv4Address(ip_addr_str)
        except ipaddress.AddressValueError:
            self.errors.append(f"Error semántico en '{name}': Dirección IP base '{ip_addr_str}' no es una IP válida (IPv4).")
            return

        try:
            cidr_prefix = int(cidr_str.strip('/'))
            if not (1 <= cidr_prefix <= 30):
                self.errors.append(f"Error semántico en '{name}': Máscara CIDR '{cidr_str}' fuera del rango válido [/1 - /30] para VLSM con hosts utilizables.")
                return
        except ValueError:
            self.errors.append(f"Error semántico en '{name}': Máscara '{cidr_str}' no es un formato CIDR válido.")
            return

        if any(h <= 0 for h in hosts_list):
            self.errors.append(f"Error semántico en '{name}': Todos los hosts solicitados deben ser números positivos (> 0).")
        
        if not hosts_list:
            self.errors.append(f"Error semántico en '{name}': No se especificó ninguna cantidad de hosts.")
            return

        try:
            network = ipaddress.IPv4Network(f"{ip_addr_str}{cidr_str}", strict=True) 
        except ValueError:
            self.errors.append(f"Error semántico en '{name}': La IP base '{ip_addr_str}' no es la dirección de red para la máscara '{cidr_str}'. Se esperaba '{ipaddress.IPv4Network(f'{ip_addr_str}/{cidr_prefix}', strict=False).network_address}'.")
            return
            
        max_hosts_req = max(hosts_list)
        bits_host_max = math.ceil(math.log2(max_hosts_req + 2)) 
        new_cidr_min = 32 - bits_host_max
        
        if new_cidr_min < cidr_prefix:
            self.errors.append(
                f"Error semántico en '{name}': El host más grande ({max_hosts_req}) requiere una máscara mínima de '/{new_cidr_min}'. "
                f"La máscara base '{cidr_str}' es demasiado pequeña para contenerlo."
            )
            
        sorted_hosts = sorted(hosts_list, reverse=True)
        total_block_size = 0
        
        for num_hosts in sorted_hosts:
            bits_host = math.ceil(math.log2(num_hosts + 2))
            block_size = 2 ** bits_host
            total_block_size += block_size
        
        if total_block_size > network.num_addresses:
            self.errors.append(
                f"Error semántico en '{name}': El espacio total requerido para todas las subredes ({total_block_size} direcciones) excede "
                f"el tamaño total de la red base '{network}' ({network.num_addresses} direcciones)."
            )

    def generate_ir(self):
        """
        Genera código intermedio (IR) para los bloques válidos después del análisis semántico.
        """
        emitter = IREmitter()
        for i, block in enumerate(self.blocks):
            name = block.get('name', f'block{i+1}')
            ip = block['ip_address']
            mask = block['subnet_mask']
            hosts = block['num_hosts']

            emitter.emit("LOAD_NET", f"{ip}{mask}", None, name)
            for idx, h in enumerate(hosts):
                emitter.emit("ALLOC_SUBNET", name, h, f"{name}_sub{idx+1}")
            emitter.emit("CALC_VLSM", name, None, None)
            emitter.emit("EXPORT_EXCEL", name, None, None)
            emitter.emit("END_BLOCK", None, None, name)

        return emitter