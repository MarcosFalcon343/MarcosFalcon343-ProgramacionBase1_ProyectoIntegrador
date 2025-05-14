import os
from datetime import datetime

from Model.Token import Token


class Lexer:
    def __init__(self, filename):
        self.tokens = []
        with open(filename, "r", encoding="utf-8") as file:
            self.lines = file.readlines()
        self.current_level = 1
        self.indentation_length = 0
        self.line_number = 1

    def guardar_tokens(self):
        if not os.path.exists("Tokens"):
            os.makedirs("Tokens")

        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = f"Tokens/tokens_{fecha_actual}.txt"

        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            for token in self.tokens:
                archivo.write(repr(token) + "\n")

    def procesar_formatos(self, text):
        position = 0
        start_plain = 0
        while position < len(text):
            new_pos, tipo, content, processed = self.procesar_formatos_LINK(text, position)
            if not processed:
                new_pos, tipo, content, processed = self.procesar_formatos_BOLD_ITALICA(text, position)
            if not processed:
                new_pos, tipo, content, processed = self.procesar_formatos_BOLD(text, position)
            if not processed:
                new_pos, tipo, content, processed = self.procesar_formatos_ITALICA(text, position)
            if not processed:
                new_pos, tipo, content, processed = self.procesar_procesar_formatos_STRIKETHROUGH(text, position)

            if processed:
                # Agregar texto plano ANTES del decorador
                if start_plain < position:
                    plain_content = text[start_plain:position]
                    self.procesar_PLAIN_TEXT(plain_content)

                # Agregar token(s) del decorador
                if tipo == "LINK":  # Caso especial para enlaces
                    link_text, link_url = content
                    self.tokens.append(Token(
                        categoria="REFERENCES",
                        tipo="LINK_START",
                        valor="",
                        linea=self.line_number
                    ))

                    self.procesar_formatos(link_text)

                    self.tokens.append(Token(
                        categoria="URL",
                        tipo="RAW_URL",
                        valor=link_url,
                        linea=self.line_number
                    ))

                    self.tokens.append(Token(
                        categoria="REFERENCES",
                        tipo="LINK_END",
                        valor="",
                        linea=self.line_number
                    ))
                else:  # Otros formatos (BOLD, ITALICA, etc.)
                    self.tokens.append(Token(
                        categoria="FORMAT",
                        tipo=tipo,
                        valor=content,
                        linea=self.line_number
                    ))

                position = new_pos
                start_plain = position
            else:
                position += 1

        if start_plain < len(text):
            self.procesar_PLAIN_TEXT(text[start_plain:])

    def procesar_estructuras(self, line):
        position = 0
        length = 0
        while position < len(line) and line[position] in [' ', '\t']:
            if line[position] == '\t':
                length = length + 4
            elif line[position] == ' ':
                length += 1
            position += 1

        if (length -  self.indentation_length) > 0:
            self.current_level += 1
        elif (length - self.indentation_length) < 0:
            self.current_level -= 1
        self.indentation_length = length

        if not any([
            self.procesar_estructura_HEADER(line[position:]),
            self.procesar_estructura_LISTA_NO_ORDENADA(line[position:]),
            self.procesar_estructura_LISTA_ORDENADA(line[position:]),
            self.procesar_estructura_TABLE(line[position:]),
            self.procesar_estructura_CITE(line[position:]),
            self.procesar_estructura_HORIZONTAL_RULE(line[position:]),
            self.procesar_estructura_SALTO_LINEA(line[position:])
        ]):
            self.procesar_formatos(line[position:])


    def analizar(self):
        for line in self.lines:
            self.procesar_estructuras(line)
            self.line_number += 1

    def mostrar_tokens(self):
        for token in self.tokens:
            print(token)

    # procesadores de estructuras
    def procesar_estructura_HEADER(self, line):
        if line.startswith("#"):
            nivel = 0
            while nivel < len(line) and line[nivel] == "#" and line[nivel] != '\n':
                nivel += 1

            self.tokens.append(Token(
                categoria="CONTENT",
                tipo="HEADER",
                valor="",
                nivel=nivel,
                linea=self.line_number
            ))

            self.procesar_formatos(line[nivel + 1:])
            return True
        else:
            return False

    def procesar_estructura_LISTA_NO_ORDENADA(self, line):
        if line.startswith("* ") or line.startswith("+ ") or line.startswith("- "):

            self.tokens.append(Token(
                categoria="CONTENT",
                tipo="LISTA_NO_ORDENADA",
                valor="",
                nivel=self.current_level,
                linea=self.line_number
            ))
            self.procesar_formatos(line[2:])

            return True
        else:
            return False

    def procesar_estructura_LISTA_ORDENADA(self,line):
        spl = line.split(". ")
        if len(line) >= 3 and spl[0][0].isdigit():
            self.tokens.append(Token(
                categoria="CONTENT",
                tipo="LISTA_ORDENADA",
                valor="",
                nivel=self.current_level,
                linea=self.line_number
            ))
            self.procesar_formatos(spl[1])

            return True
        else:
            return False

    def procesar_estructura_CITE(self, line):
        if line.startswith(">"):
            self.tokens.append(Token(
                categoria="CONTENT",
                tipo="CITE",
                valor="",
                nivel=self.current_level,
                linea=self.line_number
            ))
            self.procesar_estructuras(line[1:])
            return True
        else:
            return False

    def procesar_estructura_TABLE(self, line):
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            return False
        self.tokens.append(Token(
            categoria="ESTRUCTURA",
            tipo="TABLE_ROW",
            valor="",
            linea=self.line_number
        ))
        celdas = [celda.strip() for celda in line[1:-1].split("|")]

        if all("-" in celda for celda in celdas):
            self.tokens.append(Token(
                categoria="ESTRUCTURA",
                tipo="TABLE_SEPARATOR",
                valor="",
                linea=self.line_number
            ))
            return True

        for celda in celdas:
            self.tokens.append(Token(
                categoria="ESTRUCTURA",
                tipo="TABLE_CELL_START",
                valor="",
                linea=self.line_number
            ))

            if celda:
                self.procesar_formatos(celda)

            self.tokens.append(Token(
                categoria="ESTRUCTURA",
                tipo="TABLE_CELL_END",
                valor="",
                linea=self.line_number
            ))

        return True

    def procesar_estructura_HORIZONTAL_RULE(self, line):
        if line.startswith("---") or line.startswith("***") or line.startswith("___") and len(line) <= 4:
            self.tokens.append(Token(
                categoria="SEPARATOR",
                tipo="HORIZONTAL_RULE",
                linea=self.line_number,
                valor=""))
            return True
        else:
            return False

    def procesar_estructura_SALTO_LINEA(self, line):
        if line.startswith("\n"):
            self.tokens.append(Token(
                categoria="SEPARATOR",
                tipo="LINE_BREAK",
                linea=self.line_number,
                valor=""))
            return True
        else:
            return False

    # procesar formatos
    def procesar_formatos_BOLD(self, text, position):
        if position + 2 > len(text):
            return position, None, None, False
        delimiter = text[position:position + 2]
        if delimiter not in ("**", "__"):
            return position, None, None, False
        end = text.find(delimiter, position + 2)
        if end == -1:
            return position, None, None, False
        content = text[position + 2:end]
        return end + 2, "BOLD", content, True  # (new_pos, tipo, contenido, processed)

    def procesar_formatos_ITALICA(self, text, position):
        if position >= len(text):
            return position, None, None, False
        delimiter = text[position]
        if delimiter not in ("*", "_"):
            return position, None, None, False
        end = text.find(delimiter, position + 1)
        if end == -1:
            return position, None, None, False
        content = text[position + 1:end]
        return end + 1, "ITALICA", content, True  # ¡Sin agregar token aquí!

    def procesar_formatos_BOLD_ITALICA(self, text, position):
        if position + 3 > len(text):
            return position, None, None, False

        # Delimitadores válidos (incluyendo combinaciones de ** y _)
        valid_delimiters = ("***", "___", "**_", "_**", "*__", "__*")
        delimiter = text[position:position + 3]

        if delimiter not in valid_delimiters:
            return position, None, None, False


        reversed_delimiter = delimiter[::-1]
        end = text.find(reversed_delimiter, position + 3)
        if end == -1:
            return position, None, None, False

        content = text[position + 3:end]
        return end + 3, "BOLD_ITALICA", content, True

    def procesar_procesar_formatos_STRIKETHROUGH(self, text, position):
        if position + 2 > len(text) or text[position:position + 2] != "~~":
            return position, None, None, False
        end = text.find("~~", position + 2)
        if end == -1:
            return position, None, None, False
        content = text[position + 2:end]
        return end + 2, "STRIKETHROUGH", content, True

    def procesar_formatos_LINK(self, text, position):
        if text[position] != '[':
            return position, None, None, False
        end_bracket = text.find(']', position)
        if end_bracket == -1:
            return position, None, None, False
        if end_bracket + 1 >= len(text) or text[end_bracket + 1] != '(':
            return position, None, None, False
        start_url = end_bracket + 2
        end_url = text.find(')', start_url)
        if end_url == -1:
            return position, None, None, False
        link_text = text[position + 1:end_bracket]
        link_url = text[start_url:end_url]

        return end_url + 1, "LINK", (link_text, link_url), True  # Tipo compuesto para manejar ambos

    def procesar_PLAIN_TEXT(self, content):
        if content.strip():  # Evitar espacios vacíos
            self.tokens.append(Token(
                categoria="TEXT",
                tipo="PLAIN",
                valor=content,
                linea=self.line_number
            ))