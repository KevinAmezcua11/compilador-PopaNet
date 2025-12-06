# vm.py
import struct
from io import BytesIO

class VLSMVirtualMachine:
    """
    VM compatible con el formato generado por object_code_generator.py
    Provee dos formas de carga:
      - load(path) : carga desde archivo .vlsmobj
      - load_from_bytes(b) : carga desde bytes en memoria
    Y ejecuta con run_and_collect() devolviendo la salida como string.
    """

    def __init__(self):
        self.instructions = []
        self.strings = []
        self.pc = 0

    def reset(self):
        self.instructions = []
        self.strings = []
        self.pc = 0

    # --- cargar desde archivo ---
    def load(self, path):
        with open(path, "rb") as f:
            data = f.read()
        self._parse_bytes(data)

    # --- cargar desde bytes (en memoria) ---
    def load_from_bytes(self, data_bytes: bytes):
        self._parse_bytes(data_bytes)

    def _parse_bytes(self, data):
        # header
        if len(data) < 8 or data[:7] != b"VLSMOBJ":
            raise ValueError("Archivo inválido o corrupto (falta encabezado VLSMOBJ)")

        version = data[7]
        offset = 8

        # string table count (2 bytes)
        if offset + 2 > len(data):
            raise ValueError("Archivo truncado al leer tabla de strings")
        str_count = struct.unpack(">H", data[offset:offset+2])[0]
        offset += 2

        self.strings = []
        for _ in range(str_count):
            if offset + 2 > len(data):
                raise ValueError("Archivo truncado leyendo longitud de string")
            slen = struct.unpack(">H", data[offset:offset+2])[0]
            offset += 2
            if offset + slen > len(data):
                raise ValueError("Archivo truncado leyendo string")
            s = data[offset:offset+slen].decode("utf-8")
            offset += slen
            self.strings.append(s)

        # instructions count (4 bytes)
        if offset + 4 > len(data):
            raise ValueError("Archivo truncado leyendo count instrucciones")
        instr_count = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4

        self.instructions = []
        # read each instruction
        for i in range(instr_count):
            if offset >= len(data):
                raise ValueError("Archivo truncado en instrucciones")
            opcode = data[offset]
            offset += 1
            operands = []
            for _ in range(3):
                if offset >= len(data):
                    raise ValueError("Archivo truncado en operandos")
                otype = data[offset]
                offset += 1
                if otype == 0:  # NONE
                    operands.append(None)
                elif otype == 1:  # INT (4 bytes)
                    if offset + 4 > len(data):
                        raise ValueError("Archivo truncado en int operand")
                    val = struct.unpack(">i", data[offset:offset+4])[0]
                    offset += 4
                    operands.append(val)
                elif otype == 2:  # STR_INDEX (2 bytes)
                    if offset + 2 > len(data):
                        raise ValueError("Archivo truncado en str index")
                    idx = struct.unpack(">H", data[offset:offset+2])[0]
                    offset += 2
                    if idx < 0 or idx >= len(self.strings):
                        raise IndexError("Índice de string fuera de rango")
                    operands.append(self.strings[idx])
                else:
                    raise ValueError(f"Tipo de operando desconocido: {otype}")
            self.instructions.append((opcode, operands))

        self.pc = 0

    # --- ejecutar y devolver salida como string ---
    def run_and_collect(self):
        out_lines = []
        out_lines.append(">> VM: Inicio de ejecución")
        while self.pc < len(self.instructions):
            opcode, operands = self.instructions[self.pc]
            self._execute_instruction(opcode, operands, out_lines)
            self.pc += 1
        out_lines.append(">> VM: Fin de ejecución")
        return "\n".join(out_lines)

    def _execute_instruction(self, opcode, operands, out_lines):
        # operands = [arg1, arg2, arg3]
        a, b, c = operands

        # Opcodes acordes a object_code_generator.py
        if opcode == 0x01:  # BEGIN_BLOCK
            out_lines.append(f"[BEGIN_BLOCK] name={c}")
        elif opcode == 0x02:  # END_BLOCK
            out_lines.append(f"[END_BLOCK] name={c}")
        elif opcode == 0x10:  # SET_IP
            out_lines.append(f"[SET_IP] ip={a}")
        elif opcode == 0x11:  # SET_MASK
            out_lines.append(f"[SET_MASK] mask={a}")
        elif opcode == 0x12:  # ALLOC_SUBNET
            out_lines.append(f"[ALLOC_SUBNET] name={a}, hosts={b}")
        elif opcode == 0x20:  # LOAD_NET
            out_lines.append(f"[LOAD_NET] net={a}, block={c}")
        elif opcode == 0x21:  # CALC_VLSM
            out_lines.append(f"[CALC_VLSM] block={a}")
        elif opcode == 0x22:  # EXPORT_EXCEL
            out_lines.append(f"[EXPORT_EXCEL] block={a}")
        else:
            out_lines.append(f"INSTRUCCIÓN DESCONOCIDA OPCODE={opcode} en pc={self.pc}")

