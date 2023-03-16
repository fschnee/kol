from kol.operator import *

# The operators themselves
mul   = Operator('mul', '*',   lambda binopNode, interp: interp.eval_ast(binopNode.lhs) * interp.eval_ast(binopNode.rhs))
div   = Operator('div', '/',   lambda b, i: i.eval_ast(b.lhs) / i.eval_ast(b.rhs))
plus  = Operator('plus', '+',  lambda b, i: i.eval_ast(b.lhs) + i.eval_ast(b.rhs))
minus = Operator('minus', '-', lambda b, i: i.eval_ast(b.lhs) - i.eval_ast(b.rhs))
neg   = Operator('neg', '-',   lambda u, i: -i.eval_ast(u.expr), Category.Prefix)
ass   = Operator('ass', '=',   lambda b, i: i.set_variable(b.lhs.ident, i.eval_ast(b.rhs))) # TODO: assure lhs is identNode.

lparen = Operator('lparen', '(', None, Category.Encloser)
rparen = Operator('rparen', ')', None, Category.Encloser)
lparen.opening, lparen.closing = lparen, rparen
rparen.opening, rparen.closing = lparen, rparen

operators = [mul, div, plus, minus, neg, ass, lparen, rparen]
def find_operator(symbol: str, ops = operators): return [o for o in ops if o.symbol == symbol]

infix_operators    = [o for o in operators if o.category == Category.Infix]
prefix_operators   = [o for o in operators if o.category == Category.Prefix]
encloser_operators = [o for o in operators if o.category == Category.Encloser]

# The relationships
make_eq_prec([plus, minus])
make_gt_prec([plus, minus], [mul, neg])

make_gt_prec([mul, div, plus, minus, neg, ass], [lparen, rparen])

if __name__ == "__main__":
    from pprint import pprint
    pprint(operators, indent=4, depth=3)
