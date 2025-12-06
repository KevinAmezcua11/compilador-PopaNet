# object_code_generator.py
import struct

class ObjectCodeGenerator:

    OPCODES = {
        "BEGIN_BLOCK":   0x01,
        "END_BLOCK":     0x02,
        "SET_IP":        0x10,
        "SET_MASK":      0x11,
        "ALLOC_SUBNET":  0x12,
        "LOAD_NET":      0x20,
        "CALC_VLSM":     0x21,
        "EXPORT_EXCEL":  0x22,
    }

    def __init__(self):
        self.instructions = []
        self.string_table = []
        self.string_index = {}

    # ----------------------------------------------------------
    #  STRING TABLE
    # ----------------------------------------------------------
    def _add_string(self, value):
        """Agrega string a la tabla, devuelve índice"""
        if value is None:
            return None
        value = str(value)
        if value in self.string_index:
            return self.string_index[value]

        idx = len(self.string_table)
        self.string_table.append(value)
        self.string_index[value] = idx
        return idx

    # ----------------------------------------------------------
    #  ADD IR INSTRUCTION
    # ----------------------------------------------------------
    def add_instruction(self, instr):
        """Recibe un objeto IRInstruction (op, arg1, arg2, result)."""
        self.instructions.append(instr)

        # Los strings deben guardarse en la tabla
        for param in (instr.arg1, instr.arg2, instr.result):
            if isinstance(param, str):
                self._add_string(param)

    # ----------------------------------------------------------
    #  BINARY ENCODING
    # ----------------------------------------------------------
    def _encode_operand(self, operand):
        """Codifica el operando en bytes."""
        if operand is None:
            return b"\x00"  # tipo NONE

        # ENTERO
        if isinstance(operand, int):
            return b"\x01" + struct.pack(">i", operand)

        # STRING: se guarda como índice
        idx = self._add_string(operand)
        return b"\x02" + struct.pack(">H", idx)

    # ----------------------------------------------------------
    #  GENERAR ARCHIVO OBJETO
    # ----------------------------------------------------------
    def generate_object_code(self):
        """Devuelve el archivo objeto (bytes)."""

        data = bytearray()

        # HEADER
        data.extend(b"VLSMOBJ")   # firma (7 bytes)
        data.append(1)            # versión (1 byte)

        # TABLA DE STRINGS
        data.extend(struct.pack(">H", len(self.string_table)))
        for s in self.string_table:
            encoded = s.encode("utf-8")
            data.extend(struct.pack(">H", len(encoded)))
            data.extend(encoded)

        # INSTRUCCIONES
        data.extend(struct.pack(">I", len(self.instructions)))

        for instr in self.instructions:
            opcode = self.OPCODES.get(instr.op, 0xFF)
            data.append(opcode)

            # arg1, arg2, result
            for op in (instr.arg1, instr.arg2, instr.result):
                data.extend(self._encode_operand(op))

        return bytes(data)

    # ----------------------------------------------------------
    #  GENERAR LISTING HUMANO
    # ----------------------------------------------------------
    def generate_listing(self):
        """Devuelve representación estilo ensamblador."""
        text = []
        for i, instr in enumerate(self.instructions, start=1):
            args = []
            for a in (instr.arg1, instr.arg2, instr.result):
                if a is not None:
                    args.append(repr(a))
            text.append(f"{i:04d}: {instr.op} " + ", ".join(args))
        return "\n".join(text)
