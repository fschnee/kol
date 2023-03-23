from kol import operators as ops
from kol import lexer as kollex
from kol import cst as kolcst

from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class StmtSeq:
    first: Any
    rest:  'StmtSeq' | Any

@dataclass
class BinopNode:
    lhs: Any # ExprNode
    op: kollex.Glyph # | Operator.Operator
    rhs: Any

@dataclass
class UnopNode:
    op: kollex.Glyph # | Operator.Operator
    expr: Any # ExprNode

@dataclass
class IdentNode:
    ident: kollex.Text | str

@dataclass
class FnDef:
    body: None | StmtSeq = None
    params: List[str] = field(default_factory = lambda: [])

@dataclass
class FnCall:
    fn: str | FnDef
    args: List[Any] = field(default_factory = lambda: [])

@dataclass
class If:
    cond: Any
    true: FnDef
    false: FnDef | None

def parse_stmts_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'simple-last': return parse(cst.stmt)
    elif branch == 'last':        return parse(cst.stmt)
    elif branch == 'last2':       return parse(cst.stmt)
    elif branch == 'empty':       return None
    elif branch == 'multiple':    return StmtSeq(parse(cst.stmt), parse(cst.stmts))

def parse_stmt_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'block':       return FnCall(FnDef(parse(cst.fnblock)))
    elif branch == 'empty-block': return FnCall(FnDef())
    elif branch == 'expr-stmt':   return parse(cst.expr)
    else: print('BRANCH NOT FOUND(kol.ast.parse_stmt_rule)', branch)

def parse_expr_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'binop':       return BinopNode( parse(cst.partial.lhs), cst.partial.binop.op, parse(cst.rhs) )
    elif branch == 'simple-expr': return parse(cst.expr)
    else: print('BRANCH NOT FOUND(kol.ast.parse_expr_node)', branch)

def parse_expr2_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'unop':               return UnopNode(cst.unop.op, parse(cst.expr))
    elif branch == 'fncall-noargs':      return FnCall(cst.ident.ident.text)
    elif branch == 'fncall':             return FnCall(cst.ident.ident.text, parse(cst.fncallargs))
    elif branch == 'anon-fncall':        return FnCall('kol.internal.identity', parse(cst.fncallargs))
    elif branch == 'anon-fncall-noargs': return FnCall('kol.internal.identity')
    elif branch == 'fndef':              return parse(cst.fndef)
    elif branch == 'ident':              return parse(cst.ident)
    elif branch == 'ifexpr':             return parse(cst.ifexpr)
    else: print('BRANCH NOT FOUND(kol.ast.parse_expr2_node)', branch)

def parse_ident_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'single':   return IdentNode(cst._ident.ident.text.strip())
    elif branch == 'multiple': return IdentNode(cst._ident.ident.text.strip() + ' ' + parse(cst.ident).ident)

def parse_fncallargs_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'single':   return [parse(cst.expr)]
    elif branch == 'multiple': return [parse(cst.first)] + parse(cst.rest)

def parse_fndef_rule(cst: kolcst.UnwindableMatch, branch: str):
    if   branch == 'with-args':    return FnDef(parse(cst.stmts), parse(cst.fncallargs))
    elif branch == 'without-args': return FnDef(parse(cst.stmts))
    elif branch == 'minimal':      return FnDef(parse(cst.stmts))
    else: print('BRANCH NOT FOUND(kol.ast.parse_fndef_rule)', branch)

def parse_binopleftpartials_rule(cst: kolcst.UnwindableMatch, branch: str):
    if branch == 'single': return parse(cst.first.lhs), cst.first.binop.op
    else:
        subexpr, remaining_left_op = parse(cst.rest)
        return BinopNode(parse(cst.first.lhs), cst.first.binop.op, subexpr), remaining_left_op


def parse_ifexpr_rule(cst: kolcst.UnwindableMatch, branch: str):
    if branch not in ['regular', 'lpartial', 'lpartial-named', 'rpartial', 'rpartial-named']:
        print('BRANCH NOT FOUND(kol.ast.parse_ifexpr_rule)', branch)
        exit(1)

    ret, root, cst, varname = If(None, None, None), cst, cst.arms, 'it'
    curr = ret

    if branch in ['lpartial-named', 'rpartial-named']: varname = parse(root.varname).ident
    if branch in ['lpartial-named', 'lpartial']: rootexpr, remaining_left_op = parse(root.binopleftpartials)

    if branch in ['lpartial', 'rpartial', 'lpartial-named', 'rpartial-named']: # Create a scope for the partial expression so it's only evaluated once.
        ret = FnCall(FnDef(StmtSeq(BinopNode(
            IdentNode(varname),
            kollex.Glyph('='),
            FnCall(
                'kol.internal.identity', # Make the precedence unambigous in case it's a custom operator and the user forgot to assign precedence.
                [ parse(root.expr) if branch not in ['lpartial', 'lpartial-named'] else rootexpr ]
            )
        ), ret)))

    while cst != None:
        arm, _, armbranch = cst.arm, *cst.arm._type.split(':')

        if armbranch == 'ellipsis':
            curr.false = FnDef(parse(arm.stmts))
            return ret # NOTE: This discards the rest of the tree if it exists.
        elif armbranch in ['expr', 'lp-expr', 'rpartial']:
            if curr.cond is not None:
                curr.false = FnDef(If(None, None, None))
                curr       = curr.false.body
            if   armbranch == 'expr':     curr.cond = parse(arm.expr)
            elif armbranch == 'lp-expr':  curr.cond = BinopNode(IdentNode(varname), remaining_left_op, parse(arm.expr))
            elif armbranch == 'rpartial': curr.cond = BinopNode(IdentNode(varname), arm.binoprightpartial.binop.op, parse(arm.binoprightpartial.rhs))
            curr.true = FnDef(parse(arm.stmts))

        cst = cst.rest if cst._type.split(':')[1] == 'multiple' else None
    return ret

parsemap = {
    "stmt":  parse_stmt_rule,
    "stmts": parse_stmts_rule,

    "expr'": parse_expr2_rule,
    "expr":  parse_expr_rule,

    "ident": parse_ident_rule,

    "fncallargs": parse_fncallargs_rule,
    "fndef": parse_fndef_rule,

    "binopleftpartials": parse_binopleftpartials_rule,
    "ifexpr": parse_ifexpr_rule,
}

def parse(cstnode: kolcst.UnwindableMatch, parsemap = parsemap):
    rule, branch = cstnode._type.split(':')
    try: return parsemap[ rule ](cstnode, branch)
    except KeyError as e: print('KeyError', e)

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
    if _ast is None: return None # Silently error. TODO: is this the correct approach ?

    # Simplify some structures, sort out operator precedence.
    t = type(_ast)

    if   t is BinopNode:    return binop_shunting_yard(_ast)
    elif t is UnopNode:     return UnopNode( ops.find_operator(_ast.op.text, ops.prefix_operators)[0], base_rewrite(_ast.expr) )
    elif t is IdentNode:    return IdentNode( _ast.ident.strip() )
    elif t is StmtSeq:      return StmtSeq( base_rewrite(_ast.first), base_rewrite(_ast.rest) )
    elif t is FnCall:       return FnCall( base_rewrite(_ast.fn) if type(_ast.fn) is not str else _ast.fn, [base_rewrite(a) for a in _ast.args] )
    elif t is FnDef:        return FnDef( base_rewrite(_ast.body), _ast.params )
    elif t is If:           return If( base_rewrite(_ast.cond), base_rewrite(_ast.true), base_rewrite(_ast.false) )
    else: print('Error(base_rewrite): Unrecognized ast', t, _ast)

rewrites = [base_rewrite]

def parse_and_rewrite(cstnode: kolcst.UnwindableMatch, parsemap = parsemap, rewrites = rewrites):
    ast = parse(cstnode)
    for r in rewrites: ast = r(ast)
    return ast

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv

    with open(argv[1]) as f: pprint( parse_and_rewrite( kolcst.parse( f.read() )[0] ), indent=4, width=100 )