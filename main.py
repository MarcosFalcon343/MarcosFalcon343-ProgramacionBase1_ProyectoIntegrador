from lexer import Lexer
from parser import Parser

if __name__ == "__main__":
    lexer = Lexer("markdownFile.md")
    lexer.analizar()
    lexer.guardar_tokens()

    parser = Parser(lexer.tokens)
    parser.parse()
    parser.guardar_ast(parser.ast)