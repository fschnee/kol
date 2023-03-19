from kol import interpdata, ast

def convert(_ast):
    t = type(_ast)

    if t is ast.StmtSeq:
        # Serialize the statements
        stmts = []
        while type(_ast) is ast.StmtSeq:
            stmts.append( convert(_ast.first) )
            _ast = _ast.rest
        stmts.append( convert(_ast) )
        return stmts

    elif t is ast.BinopNode:
        if _ast.op.name == 'ass': return interpdata.Assign(_ast.lhs.ident, convert(_ast.rhs))
        else: return interpdata.KolFnCall(_ast.op.name, [convert(_ast.lhs), convert(_ast.rhs)])
    
    elif t is ast.IdentNode:
        try: return interpdata.KolInt(int(_ast.ident))
        except: return interpdata.Lookup(_ast.ident)
    
    elif t is ast.EncloserNode: return convert(_ast.expr) # hardcoded to () for now
    
    elif t is ast.UnopNode: return interpdata.KolFnCall('minus', [interpdata.KolInt(0), convert(_ast.expr)]) # hardcoded to - for now
    

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv
    from kol import cst

    with open(argv[1]) as f:
        pprint( convert( ast.parse_and_rewrite( cst.parse( f.read() )[0] ) ), indent=4 )