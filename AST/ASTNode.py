class ASTNode:
    def __init__(self, node_type, level=0, value=None):
        self.node_type = node_type
        self.value = value
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def __repr__(self, indent=0):
        return ""

