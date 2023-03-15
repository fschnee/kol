# This ast has operator precedence correct.

import kol.operator as ops
import kol.ast as ast
import kol.cst as cst

from dataclasses import dataclass

class ExprNode: pass

@dataclass
class BinopNode(ExprNode):
    lhs: ExprNode
    op: ops.Operator
    rhs: ExprNode

@dataclass
class UnopNode(ExprNode):
    op: ops.Operator
    expr: ExprNode

@dataclass
class EncloserNode(ExprNode):
    op: ops.Operator
    expr: ExprNode

@dataclass
class IdentNode(ExprNode):
    ident: str

def shunting_yard_handle_same_precedence(op, stack, opstack):
    if op.assoc == ops.Associativity.Right: pass
    elif op.assoc == ops.Associativity.Left:
        while len(opstack) and op.precedence_to(opstack[-1]) == ops.Precedence.Equal: stack.append(opstack.pop())
    elif op.assoc == ops.Associativity.NonAssoc:
        print('ERROR: Non-associative operator!', op)
        exit(1) # TODO: throw descriptive exception instead.

    return stack, opstack

def binop_shunting_yard(_ast: ast.BinopNode):
    # Basically we serialize the tree again and use shunting-yard to convert the
    # expression into postfix notation.
    # From there, a simple algorithm can be used to make that into a tree again.
    stack, opstack = [], []

    curr = _ast
    while type(curr) == ast.BinopNode:
        stack.append( parse(curr.lhs) )

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

    stack = [*stack, parse(curr), *reversed(opstack) ]

    # So far the stack are just loose nodes in postfix notation, now we transform it into a tree.
    nodes = []
    while len(stack):
        curr = stack.pop(0)
        if type(curr) is ops.Operator: curr = BinopNode(nodes.pop(-2), curr, nodes.pop())
        nodes.append(curr)

    return nodes[0] # The root node.

def parse(_ast):
    t = type(_ast)

    if   t is ast.BinopNode:    return binop_shunting_yard(_ast)
    if   t is ast.UnopNode:     return UnopNode(     ops.find_operator(_ast.op.text, ops.prefix_operators)[0],   parse(_ast.expr) )
    elif t is ast.EncloserNode: return EncloserNode( ops.find_operator(_ast.op.text, ops.encloser_operators)[0], parse(_ast.expr) )
    elif t is ast.IdentNode:    return IdentNode( _ast.ident.text.strip() )

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv

    with open(argv[1]) as f:
        pprint( parse( ast.parse( cst.parse( f.read() )[0] ) ), indent=4 )