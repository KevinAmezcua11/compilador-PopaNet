# ir.py
class IRInstruction:
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __repr__(self):
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.result})"

class IREmitter:
    def __init__(self):
        self.instructions = []

    def emit(self, op, arg1=None, arg2=None, result=None):
        instr = IRInstruction(op, arg1, arg2, result)
        self.instructions.append(instr)

    def dump(self):
        """
        Devuelve una representación legible del IR.
        """
        return "\n".join([str(i) for i in self.instructions])
