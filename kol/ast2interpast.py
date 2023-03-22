from kol import interpast as tree, ast

def convert_stmtseq(_ast, convertmap): # Serialize the statements into a list.
    stmts = []
    while type(_ast) is ast.StmtSeq:
        stmts.append( convert(_ast.first, convertmap) )
        _ast = _ast.rest
    stmts.append( convert(_ast, convertmap) )
    return stmts

def convert_binopnode(_ast, convertmap):
    if _ast.op.name == 'ass': return tree.Assign(_ast.lhs.ident, convert(_ast.rhs, convertmap)) # Hardcoded for now
    else: return tree.KolFnCall(_ast.op.name, [convert(_ast.lhs, convertmap), convert(_ast.rhs, convertmap)])

def convert_identnode(_ast, convertmap):
    try: return tree.KolInt(int(_ast.ident))
    except: return tree.Lookup(_ast.ident)

def convert_unopnode(_ast, convertmap):
    return tree.KolFnCall('minus', [tree.KolInt(0), convert(_ast.expr)]) # hardcoded to - for now.
def convert_fncall(_ast, convertmap):
    return tree.KolFnCall(_ast.fn if type(_ast.fn) is str else convert(_ast.fn, convertmap), [convert(a, convertmap) for a in _ast.args])
def convert_fndef(_ast, convertmap):
    b = _ast.body if _ast.body is not None else []
    b = convert(b) # May be StmtSeq or just a single statement, thats why we force in into a list below.
    return tree.KolFn([a.ident.text for a in _ast.params], b if type(b) is list else [b])

convertmap = {
    ast.StmtSeq: convert_stmtseq,
    ast.BinopNode: convert_binopnode,
    ast.IdentNode: convert_identnode,
    ast.UnopNode: convert_unopnode,
    ast.FnCall: convert_fncall,
    ast.FnDef: convert_fndef,
}

def convert(_ast, convertmap = convertmap): return convertmap[type(_ast)](_ast, convertmap)

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv
    from kol import cst

    with open(argv[1]) as f: pprint( convert( ast.parse_and_rewrite( cst.parse( f.read() )[0] ) ), indent=4 )