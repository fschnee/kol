from kol import ast2, operator as ops

def interp_binop(ast: ast2.BinopNode):
    if   ast.op is ops.plus:  return interp(ast.lhs) + interp(ast.rhs) 
    elif ast.op is ops.minus: return interp(ast.lhs) - interp(ast.rhs)
    elif ast.op is ops.mul:   return interp(ast.lhs) * interp(ast.rhs)
    elif ast.op is ops.div:   return interp(ast.lhs) / interp(ast.rhs)
    else:
        print('[kol.interp.interp_binop] Uninplemented operator', ast.op)
        exit(1)

def interp_unop(ast: ast2.UnopNode):
    if ast.op is ops.neg: return -interp(ast.expr)
    else:
        print('[kol.interp.interp_unop] Uninplemented operator', ast.op)
        exit(1)

def interp(ast: ast2.ExprNode):
    t = type(ast)

    if   t is ast2.BinopNode:    return interp_binop(ast)
    elif t is ast2.UnopNode:     return interp_unop(ast)
    elif t is ast2.EncloserNode: return interp(ast.expr) # TODO: check op. () vs {}.
    elif t is ast2.IdentNode:    return 1 # TODO: placeholder.

if __name__ == "__main__":
    from sys import argv
    from kol import ast, cst

    with open(argv[1]) as f: print( interp( ast2.parse( ast.parse( cst.parse( f.read() )[0] ) ) ) )