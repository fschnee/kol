from dataclasses import dataclass
from kol import interpdata as tree, ast_to_interp

@dataclass
class Interpreter:
    variables = {}
    on = {
        tree.KolInt:    lambda _, ast: ast,
        tree.KolFloat:  lambda _, ast: ast,
        tree.KolFn:     lambda _, ast: ast,
        tree.Lookup:    lambda s, ast: s.handle_lookup(ast),
        tree.Assign:    lambda s, ast: s.handle_assign(ast),
        tree.KolFnCall: lambda s, ast: s.handle_fn_call(ast),
    }

    def handle_lookup(self, ast: tree.Lookup): return self.variables[ast.name]
    def handle_assign(self, ast: tree.Assign): self.variables[ast.name] = ast.value; return ast.value
    def handle_fn_call(self, ast: tree.KolFnCall):
        if   type(ast.fn) is str:        return self.handle_lookup(tree.Lookup(ast.fn)).body(self, *ast.params)
        elif type(ast.fn) is tree.KolFn: return ast.fn.body(self, *ast.params)
        else: print('error'); exit(1)

    def eval_ast(self, ast):
        if type(ast) is not list: ast = [ast]
        for _ast in ast: v = self.on[type(_ast)](self, _ast)
        return v

if __name__ == "__main__":
    from sys import argv
    from kol import ast, ast, cst

    i = Interpreter()
    i.variables['minus'] = tree.KolFn(lambda i, a, b: tree.KolInt(i.eval_ast(a).value - i.eval_ast(b).value))
    i.variables['plus']  = tree.KolFn(lambda i, a, b: tree.KolInt(i.eval_ast(a).value + i.eval_ast(b).value))
    i.variables['mul']   = tree.KolFn(lambda i, a, b: tree.KolInt(i.eval_ast(a).value * i.eval_ast(b).value))
    i.variables['div']   = tree.KolFn(lambda i, a, b: tree.KolInt(int(i.eval_ast(a).value / i.eval_ast(b).value)))
    with open(argv[1]) as f: ast = ast_to_interp.convert( ast.parse_and_rewrite( cst.parse( f.read() )[0] ) )
    print( i.eval_ast(ast) )