class IROptimizer:
    def optimize(self, instructions):
        optimized = []
        last = None

        for instr in instructions:
            # Eliminar instrucciones duplicadas consecutivas
            if last and instr.op == last.op and instr.arg1 == last.arg1:
                continue

            # Eliminar bloques vacíos
            if instr.op == "END_BLOCK" and last and last.op == "BEGIN_BLOCK":
                optimized.pop()
                last = None
                continue

            optimized.append(instr)
            last = instr

        return optimized
