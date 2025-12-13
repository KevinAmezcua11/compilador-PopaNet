# code_generator_asm.py
from vlsm_calc import calculate_vlsm

class ASMCodeGenerator:
    """
    Genera código ensamblador 8086 que construye la configuración del router.
    Versión optimizada y funcional para EMU8086.
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
        Procesa las instrucciones IR y genera código ensamblador 8086.
        """
        # Generar configuración primero para obtener strings
        config_lines = self._generate_config()
        
        # Construir el programa ensamblador
        self._build_asm_program(config_lines)
        
        return "\n".join(self.output)
    
    def _generate_config(self):
        """Genera las líneas de configuración del router."""
        config = []
        config.append("!")
        config.append("hostname Router-VLSM")
        config.append("!")
        
        for instr in self.instructions:
            if instr.op == "BEGIN_BLOCK":
                self.current_block = instr.arg1
                self.hosts_list = []
                config.append(f"! === RED: {self.current_block} ===")
            elif instr.op == "SET_IP":
                self.base_ip = instr.arg1
            elif instr.op == "SET_MASK":
                self.base_mask = instr.arg1
            elif instr.op == "ALLOC_SUBNET":
                self.hosts_list.append(instr.arg1)
            elif instr.op == "END_BLOCK":
                if self.hosts_list:
                    config.extend(self._generate_subnet_config())
        
        config.append("!")
        return config
    
    def _generate_subnet_config(self):
        """Genera configuración de subredes usando VLSM."""
        lines = []
        try:
            vlsm_results = calculate_vlsm(
                self.base_ip, 
                self.base_mask, 
                self.hosts_list, 
                self.current_block
            )
            
            interface_base = "GigabitEthernet0/0"
            
            for idx, subnet in enumerate(vlsm_results, start=1):
                subnet_name = f"{self.current_block}_sub{idx}"
                subinterface = f"{interface_base}.{self.global_subinterface_counter}"
                
                lines.append("!")
                lines.append(f"interface {subinterface}")
                lines.append(f" description {subnet_name}")
                lines.append(f" encapsulation dot1Q {self.global_subinterface_counter}")
                lines.append(f" ip address {subnet['primera_ip_utilizable']} {subnet['mascara_decimal']}")
                lines.append(f" no shutdown")
                lines.append(f"exit")
                
                self.global_subinterface_counter += 1
            
            lines.append("!")
            lines.append(f"interface {interface_base}")
            lines.append(" no shutdown")
            lines.append("exit")
                
        except Exception as e:
            lines.append(f"! Error: {e}")
        
        return lines
    
    def _escape_string(self, s):
        """Escapa caracteres especiales para ASM."""
        # Reemplazar comillas y caracteres problemáticos
        s = s.replace("'", "''")
        s = s.replace('"', '""')
        return s
    
    def _build_asm_program(self, config_lines):
        """Construye el programa completo en ensamblador 8086."""
        self.output.append("; ========================================")
        self.output.append("; Generador de Configuracion de Router")
        self.output.append("; Compilador VLSM - Codigo Ensamblador 8086")
        self.output.append("; ========================================")
        self.output.append("; INSTRUCCIONES:")
        self.output.append("; 1. Compilar con EMU8086 (F5)")
        self.output.append("; 2. Ejecutar en modo Emulador (F6)")
        self.output.append("; 3. Presionar RUN (F9)")
        self.output.append("; 4. El archivo router_config.cfg se creara")
        self.output.append("; ========================================")
        self.output.append("")
        self.output.append("ORG 100h              ; Programa .COM")
        self.output.append("")
        self.output.append("; Saltar la seccion de datos")
        self.output.append("JMP inicio")
        self.output.append("")
        self.output.append("; === SECCION DE DATOS ===")
        self.output.append("")
        self.output.append("; Mensajes del sistema")
        self.output.append("msg_inicio DB 'Generando configuracion del router...', 0Dh, 0Ah, '$'")
        self.output.append("msg_exito DB 'Configuracion generada exitosamente!', 0Dh, 0Ah")
        self.output.append("          DB 'Archivo: ROUTER.CFG', 0Dh, 0Ah, '$'")
        self.output.append("msg_error DB 'Error al crear archivo', 0Dh, 0Ah, '$'")
        self.output.append("nombre_archivo DB 'ROUTER.CFG', 0")
        self.output.append("handle DW ?")
        self.output.append("")
        self.output.append("; Lineas de configuracion")
        
        # Agregar cada línea de configuración
        for i, line in enumerate(config_lines):
            escaped_line = self._escape_string(line)
            if len(escaped_line) > 0:
                # Limitar longitud de línea para ASM (máximo 80 caracteres)
                if len(escaped_line) > 70:
                    # Dividir líneas largas
                    chunks = [escaped_line[j:j+70] for j in range(0, len(escaped_line), 70)]
                    self.output.append(f"linea{i} DB '{chunks[0]}'")
                    for k, chunk in enumerate(chunks[1:], 1):
                        self.output.append(f"       DB '{chunk}'")
                    self.output.append(f"       DB 0Dh, 0Ah")
                    self.output.append(f"len{i} EQU $ - linea{i}")
                else:
                    self.output.append(f"linea{i} DB '{escaped_line}', 0Dh, 0Ah")
                    self.output.append(f"len{i} EQU $ - linea{i}")
            else:
                self.output.append(f"linea{i} DB 0Dh, 0Ah")
                self.output.append(f"len{i} EQU 2")
        
        self.output.append("")
        self.output.append("; === SECCION DE CODIGO ===")
        self.output.append("")
        self.output.append("inicio:")
        self.output.append("    ; Mostrar mensaje inicial")
        self.output.append("    MOV DX, OFFSET msg_inicio")
        self.output.append("    MOV AH, 09h")
        self.output.append("    INT 21h")
        self.output.append("")
        self.output.append("    ; Crear archivo ROUTER.CFG")
        self.output.append("    MOV AH, 3Ch          ; Funcion crear archivo")
        self.output.append("    MOV CX, 0            ; Atributos normales")
        self.output.append("    MOV DX, OFFSET nombre_archivo")
        self.output.append("    INT 21h")
        self.output.append("    JC error_archivo     ; Si CF=1, hubo error")
        self.output.append("    MOV handle, AX       ; Guardar handle")
        self.output.append("")
        self.output.append("    ; Escribir todas las lineas")
        
        # Generar código para escribir cada línea
        for i in range(len(config_lines)):
            self.output.append(f"    ; Escribir linea {i}")
            self.output.append(f"    MOV AH, 40h")
            self.output.append(f"    MOV BX, handle")
            self.output.append(f"    MOV CX, len{i}")
            self.output.append(f"    MOV DX, OFFSET linea{i}")
            self.output.append(f"    INT 21h")
            self.output.append(f"    JC error_archivo")
        
        self.output.append("")
        self.output.append("    ; Cerrar archivo")
        self.output.append("    MOV AH, 3Eh")
        self.output.append("    MOV BX, handle")
        self.output.append("    INT 21h")
        self.output.append("")
        self.output.append("    ; Mostrar mensaje de exito")
        self.output.append("    MOV DX, OFFSET msg_exito")
        self.output.append("    MOV AH, 09h")
        self.output.append("    INT 21h")
        self.output.append("    JMP fin")
        self.output.append("")
        self.output.append("error_archivo:")
        self.output.append("    MOV DX, OFFSET msg_error")
        self.output.append("    MOV AH, 09h")
        self.output.append("    INT 21h")
        self.output.append("")
        self.output.append("fin:")
        self.output.append("    ; Terminar programa")
        self.output.append("    MOV AH, 4Ch")
        self.output.append("    INT 21h")
        self.output.append("")
        self.output.append("RET")

def generate_asm_code(ir_instructions):
    """
    Genera código ensamblador 8086 desde IR.
    """
    generator = ASMCodeGenerator(ir_instructions)
    return generator.generate()

def save_asm_to_file(code, filename="router_config.asm"):
    """
    Guarda el código ensamblador en un archivo .asm
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"✓ Código ensamblador guardado en: {filename}")