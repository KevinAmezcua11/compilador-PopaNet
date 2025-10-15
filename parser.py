# parser.py
from lexer import VLSMLexer

class VLSMParser:
    def __init__(self, tokens):
        # Inicializa el parser con la lista de tokens
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def parse(self):
        """
        Analiza la lista de tokens y construye los bloques sintácticos.
        """
        results = []
        while self.pos < len(self.tokens):
            try:
                results.append(self.parse_block())
            except SyntaxError as e:
                self.errors.append(str(e))
                self.synchronize()
        return results

    def synchronize(self):
        """
        Avanza hasta el siguiente bloque IP para recuperarse de errores.
        """
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] != 'IP':
            self.pos += 1

    def parse_block(self):
        """
        Analiza un bloque de entrada (una red).
        """
        self.expect('IP')
        ip_address = self.expect('IP_ADDRESS')
        self.expect('MASK')
        subnet_mask = self.expect('SUBNET_MASK')
        self.expect('HOSTS')
        if self.pos >= len(self.tokens) or self.tokens[self.pos][0] != 'NUMBER':
            token = self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None, '?', '?')
            raise SyntaxError(f"Se esperaba al menos un NUMBER para HOSTS pero se encontró {token[0]} en línea {token[2]}, posición {token[3]}")
        num_hosts = self.parse_hosts()
        name = None
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'NAME':
            self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'IDENTIFIER':
                name = self.tokens[self.pos][1]
                self.pos += 1
        self.expect('FIN_SENTENCIA')
        return {
            'ip_address': ip_address,
            'subnet_mask': subnet_mask,
            'num_hosts': num_hosts,
            'name': name
        }

    def parse_hosts(self):
        """
        Analiza la lista de hosts solicitados (puede ser una lista separada por comas).
        """
        hosts = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token[0] == 'NUMBER':
                hosts.append(int(token[1]))
                self.pos += 1
            elif token[0] == 'COMMA':
                self.pos += 1
            else:
                break
        return hosts

    def expect(self, token_type):
        """
        Verifica que el siguiente token sea del tipo esperado, si no lanza SyntaxError.
        """
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token[0] == token_type:
                self.pos += 1
                return token[1]
            else:
                raise SyntaxError(
                    f"Se esperaba {token_type} pero se encontró {token[0]} en línea {token[2]}, posición {token[3]}"
                )
        else:
            raise SyntaxError(f"Se esperaba {token_type} pero no hay más tokens")

    # === Para el árbol sintáctico ===
    def parse_with_tree(self):
        """
        Analiza los bloques y construye el árbol de derivación para cada uno.
        """
        self.tree = []
        results = []
        current_pos = self.pos 
        self.pos = 0
        while self.pos < len(self.tokens):
            try:
                node = self.parse_block_tree()
                results.append(node)
                self.tree.append(node)
            except SyntaxError:
                self.synchronize() 
        self.pos = current_pos
        return results

    def parse_block_tree(self):
        """
        Analiza un bloque y lo representa como un árbol sintáctico.
        """
        children = []
        children.append(('IP', self.expect('IP')))
        ip_address = self.expect('IP_ADDRESS')
        children.append(('IP_ADDRESS', ip_address))
        children.append(('MASK', self.expect('MASK')))
        subnet_mask = self.expect('SUBNET_MASK')
        children.append(('SUBNET_MASK', subnet_mask))
        children.append(('HOSTS', self.expect('HOSTS')))
        hosts = self.parse_hosts_tree()
        children.append(('HOSTS_LIST', hosts))
        name = None
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'NAME':
            children.append(('NAME', self.expect('NAME')))
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == 'IDENTIFIER':
                name = self.tokens[self.pos][1]
                children.append(('IDENTIFIER', name))
                self.pos += 1
        children.append(('FIN_SENTENCIA', self.expect('FIN_SENTENCIA')))
        root_label = name if name else "BLOCK"
        return (root_label, children)

    def parse_hosts_tree(self):
        """
        Analiza la lista de hosts y la representa como nodos hoja del árbol.
        """
        hosts = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token[0] == 'NUMBER':
                hosts.append(('NUMBER', token[1]))
                self.pos += 1
            elif token[0] == 'COMMA':
                hosts.append(('COMMA', ','))
                self.pos += 1
            else:
                break
        return hosts
