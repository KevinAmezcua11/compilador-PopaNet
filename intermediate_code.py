from ir import IREmitter

class IntermediateCodeGenerator:
    def __init__(self, blocks):
        self.blocks = blocks
        self.emitter = IREmitter()

    def generate(self):
        """
        Genera el código intermedio (IR) a partir de los bloques sintácticos.
        """
        for block in self.blocks:
            name = block.get('name', 'BloqueAnonimo')
            ip = block.get('ip_address')
            mask = block.get('subnet_mask')
            hosts = block.get('num_hosts', [])

            # BEGIN_BLOCK solo necesita el nombre
            self.emitter.emit("BEGIN_BLOCK", name, None, None)

            # SET_IP solo necesita IP
            self.emitter.emit("SET_IP", ip, None, None)

            # SET_MASK solo necesita máscara
            self.emitter.emit("SET_MASK", mask, None, None)

            # ALLOC_SUBNET sí usa los 3 argumentos
            for idx, h in enumerate(hosts):
                result = f"{name}_sub{idx+1}"
                self.emitter.emit("ALLOC_SUBNET", h, name, result)

            # END_BLOCK solo necesita el nombre
            self.emitter.emit("END_BLOCK", name, None, None)

        return self.emitter.dump()
