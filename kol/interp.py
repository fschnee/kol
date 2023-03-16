from kol import ast2, operators
from dataclasses import dataclass

def interp_binop(ast: ast2.BinopNode, interp):
    if ast.op.ast_action is not None: return ast.op.ast_action(ast, interp)
    else:
        print('[kol.interp.interp_binop] Uninplemented operator', ast.op)
        exit(1)

def interp_unop(ast: ast2.UnopNode, interp):
    if ast.op.ast_action is not None: return ast.op.ast_action(ast, interp)
    else:
        print('[kol.interp.interp_unop] Uninplemented operator', ast.op)
        exit(1)

@dataclass
class Interpreter:
    variables = {}
    operators = operators
    evalmap   = {
        ast2.BinopNode: interp_binop,
        ast2.UnopNode: interp_unop,
        ast2.EncloserNode: lambda a, i: i.eval_ast(a.expr),
        ast2.IdentNode:    lambda a, i: i.get_variable(a.ident),
        ast2.Statements:   lambda a, i: [i.eval_ast(a.first), i.eval_ast(a.rest)][-1] # TODO: serialize statements to avoid recursion-caused stack-overflow.
    }

    def eval_ast(self, ast): return self.evalmap[type(ast)](ast, self)

    def get_variable(self, name): return self.variables[name]
    def set_variable(self, name, value): self.variables[name] = value; return value

if __name__ == "__main__":
    from sys import argv
    from kol import ast, cst

    i = Interpreter()
    i.variables = {"1": 1, "2": 2, "3": 3, "4": 4, "6": 6}

    with open(argv[1]) as f: ast = ast2.parse( ast.parse( cst.parse( f.read() )[0] ) )

    print( i.eval_ast(ast) )