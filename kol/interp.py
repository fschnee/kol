from kol import interpast as tree, operator, operators, ast2interpast, ast, cst
from typing import List, Callable, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Interpreter:
    ## Parsing stuff.
    operators: List[operator.Operator]                                 = field(default_factory = lambda: [])
    # The grammar.
    cst_rules: List[cst.Rule]                                          = field(default_factory = lambda: [])
    # How to convert from the grammar to an IR.
    ast_parsemap: Dict[str, Callable[[cst.UnwindableMatch, str], Any]] = field(default_factory = lambda: [])
    # How to convert fom the IR to the interpretable format (self.on).
    ast_convertmap: Dict[type, Callable[['ast'], 'tree']]              = field(default_factory = lambda: [])

    ## Runtime stuff.
    variable_scopes = [{}]
    on = {
        tree.KolNil:    lambda _, _ast: _ast,
        tree.KolInt:    lambda _, _ast: _ast,
        tree.KolFloat:  lambda _, _ast: _ast,
        tree.KolFn:     lambda _, _ast: _ast,
        tree.Lookup:    lambda s, _ast: s.handle_lookup(_ast),
        tree.Assign:    lambda s, _ast: s.handle_assign(_ast),
        tree.KolFnCall: lambda s, _ast: s.handle_fn_call(_ast),
    }

    def lookup(self, s: str): return self.eval_ast(tree.Lookup(s)) # Shorthand.
    def handle_lookup(self, _ast: tree.Lookup):
        for scope in reversed(self.variable_scopes):
            if _ast.name in scope: return scope[_ast.name]

        from pprint import pprint
        pprint(['InterpError: Name not in any scope', _ast.name, self.variable_scopes, _ast]) # TODO: throw resumable exception ?
        exit(1)

    def assign(self, n: str, v): return self.eval_ast(tree.Assign(n, v)) # Shorthand.
    def handle_assign(self, _ast: tree.Assign):
        tgt_scope = self.variable_scopes[-1]
        for scope in reversed(self.variable_scopes):
            if _ast.name in scope: tgt_scope = scope; break
        tgt_scope[_ast.name] = self.eval_ast(_ast.value)
        return tgt_scope[_ast.name]

    def handle_fn_call(self, _ast: tree.KolFnCall):
        if   type(_ast.fn) is str:        fn = self.handle_lookup(tree.Lookup(_ast.fn))
        elif type(_ast.fn) is tree.KolFn: fn = _ast.fn
        else: 
            from pprint import pprint
            pprint(['InterpError: ast.fn is not a recognized (callable or resolvable) type', _ast])
            exit(1)

        args = list( map(lambda p: self.eval_ast(p), _ast.params) )

        # TODO: check if param count matches and eventually their types.
        self.variable_scopes.append({ k: v for k, v in zip(fn.params, args) })

        if type(fn.body) is list: ret = i.eval_ast(fn.body)
        else:                     ret = fn.body(self, args)
        
        self.variable_scopes.pop()
        return ret

    def eval_ast(self, _ast):
        if type(_ast) is not list: _ast = [_ast]
        for a in _ast: v = self.on[type(a)](self, a)
        return v

    def eval_str(self, text, cstrule = 'stmts'):
        _cst, remaining = cst.parse(text, self.cst_rules, cstrule) # TODO: check for remaining text.
        _ast  = ast.parse_and_rewrite(_cst, self.ast_parsemap)
        _ast2 = ast2interpast.convert(_ast)
        return self.eval_ast(_ast2), remaining

if __name__ == "__main__":
    from sys import argv
    from kol import ast, cst

    i = Interpreter(
        operators = operators.operators,
        cst_rules = cst.default_rules,
        ast_parsemap = ast.parsemap,
        ast_convertmap = ast2interpast.convertmap
    )
    i.assign('kol.internal.identity', tree.KolFn([], lambda i, ps: ps[0] if len(ps) == 1 else ps))
    i.assign('kol.internal.if',       tree.KolFn([], lambda i, ps: i.eval_ast(tree.KolFnCall(ps[1], []) if ps[0].value == 1 else tree.KolNil())))
    i.assign('kol.internal.ifelse',   tree.KolFn([], lambda i, ps: i.eval_ast(tree.KolFnCall(ps[1       if ps[0].value == 1 else 2], []))))

    i.assign('minus',        tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(i.lookup('lhs').value - i.lookup('rhs').value)))
    i.assign('plus',         tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(i.lookup('lhs').value + i.lookup('rhs').value)))
    i.assign('mul',          tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(i.lookup('lhs').value * i.lookup('rhs').value)))
    i.assign('div',          tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(int(i.lookup('lhs').value / i.lookup('rhs').value))))
    i.assign('eq',           tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(1 if i.lookup('lhs').value == i.lookup('rhs').value else 0)))
    i.assign('ne',           tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(1 if i.lookup('lhs').value != i.lookup('rhs').value else 0)))
    i.assign('gt',           tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(1 if i.lookup('lhs').value >  i.lookup('rhs').value else 0)))
    i.assign('gte',          tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(1 if i.lookup('lhs').value >= i.lookup('rhs').value else 0)))
    i.assign('lt',           tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(1 if i.lookup('lhs').value <  i.lookup('rhs').value else 0)))
    i.assign('lte',          tree.KolFn(['lhs', 'rhs'], lambda i, _: tree.KolInt(1 if i.lookup('lhs').value <= i.lookup('rhs').value else 0)))

    with open(argv[1]) as f: 
        ret, rem = i.eval_str( f.read() )
        print(ret)
