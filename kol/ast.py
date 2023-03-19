from kol import operators as ops
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

def shunting_yard_handle_same_precedence(op, stack, opstack):
    if op.assoc == ops.Associativity.Right: pass
    elif op.assoc == ops.Associativity.Left:
        while len(opstack) and op.precedence_to(opstack[-1]) == ops.Precedence.Equal: stack.append(opstack.pop())
    elif op.assoc == ops.Associativity.NonAssoc:
        print('ERROR: Non-associative operator!', op)
        exit(1) # TODO: throw descriptive exception instead.

    return stack, opstack

def binop_shunting_yard(_ast: BinopNode):
    # Basically we serialize the tree again and use shunting-yard to convert the
    # expression into postfix notation.
    # From there, a simple algorithm can be used to make that into a tree again.
    stack, opstack = [], []

    curr = _ast
    while type(curr) == BinopNode:
        stack.append( base_rewrite(curr.lhs) )

        op = ops.find_operator(curr.op.text, ops.infix_operators)[0]
        while len(opstack):
            prec = op.precedence_to(opstack[-1])
            if prec == ops.Precedence.Lower: stack.append(opstack.pop())
            elif prec == ops.Precedence.Higher: break
            elif prec == ops.Precedence.NoPrecedence:
                print('ERROR: No precedence specified', op, opstack[-1])
                exit(1) # TODO: throw descriptive exception instead.
            elif prec == ops.Precedence.Equal: stack, opstack = shunting_yard_handle_same_precedence(op, stack, opstack)

        opstack.append(op)

        curr = curr.rhs

    stack = [*stack, base_rewrite(curr), *reversed(opstack) ]

    # So far the stack are just loose nodes in postfix notation, now we transform it into a tree.
    nodes = []
    while len(stack):
        curr = stack.pop(0)
        if type(curr) is ops.Operator: curr = BinopNode(nodes.pop(-2), curr, nodes.pop())
        nodes.append(curr)

    return nodes[0] # The root node.

def base_rewrite(_ast):
    # Simplify some structures, sort out operator precedence
    t = type(_ast)

    if   t is BinopNode:    return binop_shunting_yard(_ast)
    elif t is UnopNode:     return UnopNode(     ops.find_operator(_ast.op.text, ops.prefix_operators)[0],   base_rewrite(_ast.expr) )
    elif t is EncloserNode: return EncloserNode( ops.find_operator(_ast.op.text, ops.encloser_operators)[0], base_rewrite(_ast.expr) )
    elif t is IdentNode:    return IdentNode( _ast.ident.text.strip() )
    elif t is StmtSeq:      return StmtSeq( base_rewrite(_ast.first), base_rewrite(_ast.rest) )

def parse(cstnode: kolcst.UnwindableMatch):
    rule, branch = cstnode._type.split(':')
    try: return parsemap[ rule ](cstnode, branch)
    except KeyError as e: print('KeyError', e)

def parse_and_rewrite(cstnode: kolcst.UnwindableMatch, rewrites = [base_rewrite]):
    ast = parse(cstnode)
    for r in rewrites: ast = r(ast)
    return ast

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv

    with open(argv[1]) as f: pprint( parse_and_rewrite( kolcst.parse( f.read() )[0] ), indent=4, width=100 )