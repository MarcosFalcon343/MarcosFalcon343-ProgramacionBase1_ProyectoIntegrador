class Token:
    def __init__(self,categoria, tipo, valor,linea, nivel = -1):
        self.categoria = categoria
        self.tipo = tipo
        self.valor = valor
        self.nivel = nivel
        self.linea = linea

    def __repr__(self):
        categoria = f"{self.categoria:<10}"
        tipo = f"{self.tipo:<18}"  # 20 caracteres, alineado a la izquierda
        linea = f"{self.linea:>5}"  # 5 caracteres, alineado a la derecha (para números)
        nivel = f"{self.nivel if self.nivel != -1 else 'none':>5}"


        return f"Token(Categoría: {categoria} Tipo: {tipo} Línea: {linea} Nivel: {nivel} Valor: {self.valor})"


