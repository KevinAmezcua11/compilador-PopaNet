# intermediate_code.py
from dataclasses import dataclass

# usa el optimizador que ya tienes (optimizer.py)
from optimizer import IROptimizer

@dataclass
class IRInstruction:
    op: str
    arg1: object = None
    arg2: object = None
    result: object = None

    def __repr__(self):
        parts = [self.op]
        for p in (self.arg1, self.arg2, self.result):
            if p is not None:
                parts.append(repr(p))
        return " ".join(parts)

class IREmitter:
    def __init__(self):
        self.instructions = []

    def emit(self, op, arg1=None, arg2=None, result=None):
        instr = IRInstruction(op, arg1, arg2, result)
        self.instructions.append(instr)
        return instr

class IntermediateCodeGenerator:
    """
    Generador de código intermedio básico que produce las instrucciones
    esperadas por object_code_generator.py
    """
    def __init__(self, blocks):
        self.blocks = blocks or []
        self.emitter = IREmitter()
        self.optimizer = IROptimizer()

    def generate(self):
        # Produce una lista de instrucciones y devuelve la lista
        for i, block in enumerate(self.blocks, start=1):
            name = block.get('name', f'block{i}')
            ip = block['ip_address']
            mask = block['subnet_mask']
            hosts = block['num_hosts']

            # BEGIN
            self.emitter.emit("BEGIN_BLOCK", None, None, name)

            # LOAD_NET o LOAD info
            self.emitter.emit("LOAD_NET", f"{ip}{mask}", None, name)

            # ALLOC_SUBNET por cada hosts solicitado
            for idx, h in enumerate(hosts):
                self.emitter.emit("ALLOC_SUBNET", name, h, f"{name}_sub{idx+1}")

            # CALC VLSM y EXPORT y END
            self.emitter.emit("CALC_VLSM", name, None, None)
            self.emitter.emit("EXPORT_EXCEL", name, None, None)

            self.emitter.emit("END_BLOCK", None, None, name)

        # return the emitter.instructions for display
        return self.emitter.instructions
