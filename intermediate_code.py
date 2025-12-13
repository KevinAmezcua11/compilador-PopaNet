from ir import IREmitter
from optimizer import IROptimizer

class IntermediateCodeGenerator:
    def __init__(self, blocks):
        self.blocks = blocks
        self.emitter = IREmitter()
        self.optimizer = IROptimizer()

    def generate(self):
        """
        Genera el código intermedio.
        """
        for block in self.blocks:
            name = block.get('name', 'BloqueAnonimo')
            ip = block.get('ip_address')
            mask = block.get('subnet_mask')
            hosts = block.get('num_hosts', [])

            # BEGIN_BLOCK
            self.emitter.emit("BEGIN_BLOCK", name, None, None)

            # SET_IP
            self.emitter.emit("SET_IP", ip, None, None)

            # SET_MASK
            self.emitter.emit("SET_MASK", mask, None, None)

            # ALLOC_SUBNET
            for idx, h in enumerate(hosts):
                result = f"{name}_sub{idx+1}"
                self.emitter.emit("ALLOC_SUBNET", h, name, result)

            # END_BLOCK
            self.emitter.emit("END_BLOCK", name, None, None)

        ir = self.emitter.instructions
        optimized_ir = self.optimizer.optimize(ir)

        return "\n".join(str(i) for i in optimized_ir)
