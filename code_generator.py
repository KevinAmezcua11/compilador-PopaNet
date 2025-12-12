from vlsm_calc import calculate_vlsm

class CodeGenerator:
    def __init__(self, ir_instructions):
        self.instructions = ir_instructions
        self.cisco_output = []  # Aquí guardamos las líneas de config (texto plano)
        self.current_block = None
        self.base_ip = None
        self.base_mask = None
        self.hosts_list = []
        self.global_subinterface_counter = 1
        
    def generate(self):
        """Genera la lógica de configuración (rellena self.cisco_output)"""
        self._add_line("!")
        self._add_line("hostname Router-VLSM")
        self._add_line("!")
        
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
        
        self._add_line("!")
        return "\n".join(self.cisco_output)

    def generate_asm_viewer(self):
        """
        Genera código ASM 8086 que:
        1. Imprime el config en pantalla.
        2. Guarda el config en un archivo 'router.csg'.
        """
        if not self.cisco_output:
            self.generate() # Asegurar que hay datos

        asm = []
        
        # --- HEADER ---
        asm.append("; Programa generado por CodeGenerator")
        asm.append("; Muestra en pantalla y guarda en archivo .CSG")
        asm.append(".MODEL SMALL")
        asm.append(".STACK 100H")
        
        # --- DATA SEGMENT ---
        asm.append(".DATA")
        asm.append("    ; Mensajes de interfaz")
        asm.append("    header      DB '=== GENERANDO CONFIGURACION ===', 13, 10, '$'")
        asm.append("    msg_ok      DB 'Archivo router.csg creado exitosamente.', 13, 10, '$'")
        asm.append("    msg_err     DB 'Error al crear el archivo.', 13, 10, '$'")
        asm.append("    filename    DB 'router.csg', 0") # Nombre del archivo (terminado en 0 para ASCIIZ)
        asm.append("    filehandle  DW ?")                # Variable para guardar el 'handle' del archivo
        
        asm.append("    ; Datos del reporte")
        
        # Convertir cada línea en variable DB
        # Calculamos la longitud real (texto + CR + LF) para usarla en la escritura a archivo
        lines_meta = [] 
        for idx, line in enumerate(self.cisco_output):
            safe_line = line.replace("'", "") 
            length = len(safe_line) + 2 # +2 por CR(13) y LF(10)
            asm.append(f"    L_{idx} DB '{safe_line}', 13, 10, '$'")
            lines_meta.append({'id': f"L_{idx}", 'len': length})
            
        asm.append("    footer      DB '=== FIN ===', 13, 10, '$'")

        # --- CODE SEGMENT ---
        asm.append(".CODE")
        asm.append("MAIN PROC")
        asm.append("    ; 1. Inicializar segmento de datos")
        asm.append("    MOV AX, @DATA")
        asm.append("    MOV DS, AX")
        
        asm.append("")
        asm.append("    ; 2. Crear el archivo (Servicio 3Ch)")
        asm.append("    MOV AH, 3Ch         ; Función Create File")
        asm.append("    MOV CX, 0           ; Atributos normales")
        asm.append("    LEA DX, filename    ; Nombre del archivo")
        asm.append("    INT 21H")
        asm.append("    JC FILE_ERROR       ; Si Carry Flag=1, hubo error")
        asm.append("    MOV filehandle, AX  ; Guardar el handle del archivo")

        asm.append("")
        asm.append("    ; 3. Mostrar encabezado en pantalla")
        asm.append("    LEA DX, header")
        asm.append("    MOV AH, 09H")
        asm.append("    INT 21H")

        asm.append("")
        asm.append("    ; 4. Bucle: Imprimir en pantalla y Escribir en archivo")
        
        for meta in lines_meta:
            lbl = meta['id']
            length = meta['len']
            
            # A) Imprimir en PANTALLA (Usa $)
            asm.append(f"    ; --- Linea {lbl} ---")
            asm.append(f"    LEA DX, {lbl}")
            asm.append( "    MOV AH, 09H")
            asm.append( "    INT 21H")
            
            # B) Escribir en ARCHIVO (Usa longitud en CX, Handle en BX)
            asm.append( "    ; Escribir en archivo")
            asm.append( "    MOV AH, 40h         ; Función Write to File")
            asm.append( "    MOV BX, filehandle  ; Cargar handle")
            asm.append(f"    MOV CX, {length}          ; Bytes a escribir")
            asm.append(f"    LEA DX, {lbl}       ; Buffer de datos")
            asm.append( "    INT 21H")
            # Nota: No verificamos error de escritura por linea para mantener el ASM simple

        asm.append("")
        asm.append("    ; 5. Cerrar el archivo (Servicio 3Eh)")
        asm.append("    MOV AH, 3Eh")
        asm.append("    MOV BX, filehandle")
        asm.append("    INT 21H")
        
        asm.append("")
        asm.append("    ; 6. Mensaje de exito y fin")
        asm.append("    LEA DX, msg_ok")
        asm.append("    MOV AH, 09H")
        asm.append("    INT 21H")
        asm.append("    JMP FIN_PROGRAMA")

        asm.append("FILE_ERROR:")
        asm.append("    LEA DX, msg_err")
        asm.append("    MOV AH, 09H")
        asm.append("    INT 21H")

        asm.append("FIN_PROGRAMA:")
        asm.append("    MOV AH, 4CH")
        asm.append("    INT 21H")
        asm.append("MAIN ENDP")
        asm.append("END MAIN")
        
        return "\n".join(asm)

    # --- Métodos auxiliares y handlers ---
    def _add_line(self, text):
        self.cisco_output.append(text)

    def _handle_begin_block(self, instr):
        self.current_block = instr.arg1
        self.hosts_list = []
        self._add_line(f"! === RED: {self.current_block} ===")
        
    def _handle_set_ip(self, instr):
        self.base_ip = instr.arg1
        
    def _handle_set_mask(self, instr):
        self.base_mask = instr.arg1
        
    def _handle_alloc_subnet(self, instr):
        self.hosts_list.append(instr.arg1)
    
    def _handle_end_block(self, instr):
        if not self.hosts_list: return
        try:
            vlsm_results = calculate_vlsm(self.base_ip, self.base_mask, self.hosts_list, self.current_block)
            interface_base = "GigabitEthernet0/0"
            
            for idx, subnet in enumerate(vlsm_results, start=1):
                subnet_name = f"{self.current_block}_sub{idx}"
                sub_id = self.global_subinterface_counter
                
                self._add_line("!")
                self._add_line(f"interface {interface_base}.{sub_id}")
                self._add_line(f" description {subnet_name}")
                self._add_line(f" encapsulation dot1Q {sub_id}")
                self._add_line(f" ip address {subnet['primera_ip_utilizable']} {subnet['mascara_decimal']}")
                self._add_line(" no shutdown")
                self._add_line(" exit")
                self.global_subinterface_counter += 1
            
            self._add_line("!")
            self._add_line(f"interface {interface_base}")
            self._add_line(" no shutdown")
            self._add_line(" exit")
                
        except Exception as e:
            self._add_line(f"! Error: {e}")

# --- Funciones globales ---

def generate_object_code(ir_instructions):
    """Interfaz para llamar al generador ASM"""
    generator = CodeGenerator(ir_instructions)
    return generator.generate_asm_viewer()

def save_to_file(code, filename="output.asm"):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"✓ Código ASM guardado en: {filename}")