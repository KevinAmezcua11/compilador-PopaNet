# code_generator.py
from vlsm_calc import calculate_vlsm

class CodeGenerator:
    """
    Genera código objeto desde código intermedio IR.
    """
    def __init__(self, ir_instructions):
        self.instructions = ir_instructions
        self.output = []
        self.current_block = None
        self.base_ip = None
        self.base_mask = None
        self.hosts_list = []
        self.global_subinterface_counter = 1
        
    def generate(self):
        """
        Procesa las instrucciones IR y genera el código objeto.
        """
        self.output.append("!")
        self.output.append("hostname Router-VLSM")
        self.output.append("!")
        
        for instr in self.instructions:
            if instr.op == "BEGIN_BLOCK":
                self._handle_begin_block(instr)
            elif instr.op == "SET_IP":
                self._handle_set_ip(instr)
            elif instr.op == "SET_MASK":
                self._handle_set_mask(instr)
            elif instr.op == "ALLOC_SUBNET":
                self._handle_alloc_subnet(instr)
            elif instr.op == "END_BLOCK":
                self._handle_end_block(instr)
        
        self.output.append("!")
        
        return "\n".join(self.output)
    
    def _handle_begin_block(self, instr):
        """Inicia un nuevo bloque de red."""
        self.current_block = instr.arg1
        self.hosts_list = []
        self.output.append(f"! === RED: {self.current_block} ===")
        
    def _handle_set_ip(self, instr):
        """Guarda la IP base."""
        self.base_ip = instr.arg1
        
    def _handle_set_mask(self, instr):
        """Guarda la máscara base."""
        self.base_mask = instr.arg1
        
    def _handle_alloc_subnet(self, instr):
        """Acumula los hosts solicitados."""
        num_hosts = instr.arg1
        self.hosts_list.append(num_hosts)
    
    def _handle_end_block(self, instr):
        """
        Genera la configuración usando vlsm_calc.py con subinterfaces GigabitEthernet
        """
        if not self.hosts_list:
            return
        
        try:
            # Calcular las subredes
            vlsm_results = calculate_vlsm(
                self.base_ip, 
                self.base_mask, 
                self.hosts_list, 
                self.current_block
            )
            
            # Usar GigabitEthernet0/0 como interfaz física base
            interface_base = "GigabitEthernet0/0"
            
            for idx, subnet in enumerate(vlsm_results, start=1):
                subnet_name = f"{self.current_block}_sub{idx}"
                
                # Configurar subinterfaz con encapsulación dot1Q
                subinterface = f"{interface_base}.{self.global_subinterface_counter}"
                
                self.output.append(f"!")
                self.output.append(f"interface {subinterface}")
                self.output.append(f" description {subnet_name}")
                self.output.append(f" encapsulation dot1Q {self.global_subinterface_counter}")
                self.output.append(f" ip address {subnet['primera_ip_utilizable']} {subnet['mascara_decimal']}")
                self.output.append(f" no shutdown")
                self.output.append(f"exit")
                
                self.global_subinterface_counter += 1
            
            # Asegurar que la interfaz física esté activa
            self.output.append(f"!")
            self.output.append(f"interface {interface_base}")
            self.output.append(f" no shutdown")
            self.output.append(f"exit")
                
        except Exception as e:
            self.output.append(f"! Error: {e}")

def generate_object_code(ir_instructions):
    """
    Generar código objeto desde IR.
    """
    generator = CodeGenerator(ir_instructions)
    return generator.generate()


def save_to_file(code, filename="router_config.cfg"):
    """
    Guarda el código objeto en un archivo .cfg
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"✓ Código objeto guardado en: {filename}")
