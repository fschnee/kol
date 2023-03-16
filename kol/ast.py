from kol import lexer as kollex
from kol import cst as kolcst

from dataclasses import dataclass
from typing import List, Any

@dataclass
class StmtSeq:
    first: Any
    rest:  Any

@dataclass
class BinopNode:
    lhs: Any # ExprNode
    op: kollex.Glyph
    rhs: Any

@dataclass
class UnopNode:
    op: kollex.Glyph
    expr: Any # ExprNode

@dataclass
class EncloserNode:
    op: kollex.Glyph
    expr: Any # ExprNode

@dataclass
class IdentNode:
    ident: kollex.Text

def parse_expr_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'binop':       return BinopNode( parse(cst.lhs), cst.binop.op, parse(cst.rhs) )
    elif branch == 'simple-expr': return parse(cst.expr)
    else: print('BRANCH NOT FOUND(kol.ast.parse_expr_node)', branch)

def parse_expr2_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'unop':               return UnopNode(cst.unop.op, parse(cst.expr))
    elif branch == 'ident':              return IdentNode(cst.ident.ident)
    elif branch.startswith('encloser-'): return EncloserNode(cst.opener.op, parse(cst.expr))
    else: print('BRANCH NOT FOUND(kol.ast.parse_expr2_node)', branch)

def parse_stmt_rule(cst: kolcst.UnwindableMatch, branch: str):
    if branch == 'expr-stmt': return parse(cst.expr)

def parse_stmts_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'single':   return parse(cst.stmt)
    elif branch == 'multiple': return StmtSeq(parse(cst.stmt), parse(cst.stmts))

parsemap = {
    "expr":  parse_expr_rule,
    "expr'": parse_expr2_rule,
    "stmt":  parse_stmt_rule,
    "stmts": parse_stmts_rule,
}

def parse(cstnode: kolcst.UnwindableMatch):
    rule, branch = cstnode._type.split(':')
    try: return parsemap[ rule ](cstnode, branch)
    except KeyError as e: print('KeyError', e)

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv

    with open(argv[1]) as f: pprint( parse( kolcst.parse( f.read() )[0] ), indent=4, width=100 )