# lexer.py
import re

class VLSMLexer:
    def __init__(self):
        # Define los patrones de tokens y su tipo
        self.tokens = [
            (r'\bIP\b', 'IP'),
            (r'\bMASK\b', 'MASK'),
            (r'\bHOSTS\b', 'HOSTS'),
            (r'\bNAME\b', 'NAME'),
            (r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', 'IP_ADDRESS'),
            (r'/\d+', 'SUBNET_MASK'),
            (r'\d+', 'NUMBER'),
            (r'[A-Za-z_][A-Za-z0-9_]*', 'IDENTIFIER'),
            (r',', 'COMMA'),
            (r';', 'FIN_SENTENCIA'),
            (r'\s+', None),
        ]

    def tokenize(self, code):
        """
        Convierte el código fuente en una lista de tokens y errores léxicos.
        """
        tokens, errors = [], []
        line_num, col_num, last_type = 1, 0, None
        while code:
            match = None
            for pattern, token_type in self.tokens:
                regex = re.compile(pattern)
                match = regex.match(code)
                if match:
                    text = match.group(0)
                    lines = text.split("\n")
                    if len(lines) > 1:
                        line_num += len(lines) - 1
                        col_num = len(lines[-1])
                    else:
                        col_num += len(text)
                    code = code[len(text):]
                    if token_type:
                        start = col_num - len(text)
                        # Solo acepta IDENTIFIER si el token anterior fue NAME
                        if token_type == 'IDENTIFIER' and last_type != 'NAME':
                            errors.append(f"Token no reconocido en línea {line_num}, pos {start}: {text}")
                        else:
                            tokens.append((token_type, text, line_num, start))
                            last_type = token_type
                    break
            if not match:
                # Si no hay coincidencia, reporta error y avanza
                fragment = code.split()[0] if code.strip() else code
                errors.append(f"Token no reconocido en línea {line_num}, pos {col_num}: {fragment}")
                code = code[len(fragment):]
                col_num += len(fragment)
        return tokens, errors
