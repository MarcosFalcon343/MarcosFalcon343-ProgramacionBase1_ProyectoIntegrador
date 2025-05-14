import os
from datetime import datetime

from AST.ASTNode import ASTNode
from Model.Token import Token


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_index = 0
        self.ast = ASTNode("DOCUMENT")
        self.stack = [self.ast]


    def guardar_ast(self, raiz):
        if not os.path.exists("AST"):
            os.makedirs("AST")

        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = f"AST/ast_{fecha_actual}.txt"

        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            self._escribir_nodo(raiz, archivo)

    def _escribir_nodo(self, nodo, archivo, nivel=0):
        espacio = "  " * nivel
        valor = f": {nodo.value}" if nodo.value is not None else ""
        archivo.write(f"{espacio}{nodo.node_type}{valor}\n")

        for hijo in nodo.children:
            self._escribir_nodo(hijo, archivo, nivel + 1)

    def parse(self):
        while self.current_index < len(self.tokens):
            current_token = self.tokens[self.current_index]

            if current_token.categoria == "CONTENT":
                self.handle_content(current_token)
            elif current_token.categoria == "TEXT":
                self.handle_text(current_token)
            elif current_token.categoria == "FORMAT":
                self.handle_format(current_token)
            elif current_token.categoria == "REFERENCES":
                self.handle_reference(current_token)
            elif current_token.categoria == "SEPARATOR":
                self.handle_separator(current_token)
            elif current_token.categoria == "ESTRUCTURA":
                self.handle_estructura(current_token)

            self.current_index += 1

        return self.ast

    def handle_content(self, token: Token):
        node = ASTNode(token.tipo)

        if token.tipo == "HEADER":
            node.value = token.nivel
            self.add_to_parent(node, token.nivel)
            self.process_children(node)

        elif "LISTA" in token.tipo:
            node.value = token.nivel
            self.handle_nesting(node, token.nivel)

        elif token.tipo == "CITE":
            node.value = token.nivel
            self.handle_nesting(node, token.nivel)

        elif token.tipo == "TABLE_ROW":
            table_node = ASTNode("TABLE")
            self.stack[-1].add_child(table_node)
            self.stack.append(table_node)
            table_node.add_child(node)

    def handle_text(self, token: Token):
        text_node = ASTNode("TEXT", value=token.valor)
        self.stack[-1].add_child(text_node)

    def handle_format(self, token: Token):
        format_node = ASTNode("FORMAT", value=token.tipo)
        self.stack[-1].add_child(format_node)

    def handle_reference(self, token: Token):
        if token.tipo == "LINK_START":
            link_node = ASTNode("LINK")
            self.stack.append(link_node)
        elif token.tipo == "RAW_URL":
            if self.stack[-1].node_type == "LINK":
                self.stack[-1].value = token.valor
        elif token.tipo == "LINK_END":
            if self.stack[-1].node_type == "LINK":
                completed_link = self.stack.pop()
                self.stack[-1].add_child(completed_link)

    def handle_separator(self, token: Token):
        sep_node = ASTNode("SEPARATOR", value=token.tipo)
        self.stack[-1].add_child(sep_node)

        if token.tipo == "LINE_BREAK":
            while len(self.stack) > 1 and not isinstance(self.stack[-1], (ASTNode)):
                self.stack.pop()

    def handle_estructura(self, token: Token):
        if token.tipo == "TABLE_CELL_START":
            cell_node = ASTNode("TABLE_CELL")
            self.stack.append(cell_node)
        elif token.tipo == "TABLE_CELL_END":
            if self.stack[-1].node_type == "TABLE_CELL":
                cell = self.stack.pop()
                self.stack[-1].add_child(cell)

    def handle_nesting(self, node: ASTNode, level: int):
        while self.stack[-1].value and self.stack[-1].value >= level:
            self.stack.pop()

        self.stack[-1].add_child(node)
        self.stack.append(node)

    def add_to_parent(self, node: ASTNode, level: int):
        parent = next(
            (n for n in reversed(self.stack) if n.value is not None and n.value < level),
            self.stack[0]
        )
        parent.add_child(node)
        self.stack.append(node)

    def process_children(self, parent_node: ASTNode):
        self.current_index += 1
        while self.current_index < len(self.tokens):
            current_token = self.tokens[self.current_index]

            if current_token.categoria == "SEPARATOR":
                break

            if current_token.categoria == "TEXT":
                text_node = ASTNode("TEXT", value=current_token.valor)
                parent_node.add_child(text_node)
            elif current_token.categoria == "FORMAT":
                format_node = ASTNode("FORMAT", value=current_token.tipo)
                parent_node.add_child(format_node)

            self.current_index += 1