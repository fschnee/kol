from kol.operator import *

# The operators themselves
mul   = Operator('mul',   '*')
div   = Operator('div',   '/')
plus  = Operator('plus',  '+')
minus = Operator('minus', '-')
neg   = Operator('neg',   '-', Category.Prefix)
ass   = Operator('ass',   '=')
eq    = Operator('eq',    '==')
ne    = Operator('ne',    '!=')
gt    = Operator('gt',    '>')
gte   = Operator('gte',   '>=')
lt    = Operator('lt',    '<')
lte   = Operator('lte',   '<=')

lparen = Operator('lparen', '(', Category.Encloser)
rparen = Operator('rparen', ')', Category.Encloser)
lparen.opening, lparen.closing = lparen, rparen
rparen.opening, rparen.closing = lparen, rparen

fnbody  = Operator('fnbody',  '{', Category.Encloser)
fnbodyc = Operator('fnbodyc', '}', Category.Encloser)
fnbody.opening,  fnbody.closing  = fnbody, fnbodyc
fnbodyc.opening, fnbodyc.closing = fnbody, fnbodyc

fnargdef  = Operator('fnargdef',  '[', Category.Encloser)
fnargdefc = Operator('fnargdefc', ']', Category.Encloser)
fnargdef.opening,  fnargdef.closing  = fnargdef, fnargdefc
fnargdefc.opening, fnargdefc.closing = fnargdef, fnargdefc

operators = [mul, div, plus, minus, neg, ass, eq, ne, gt, gte, lt, lte, lparen, rparen, fnbody, fnbodyc, fnargdef, fnargdefc]
def find_operator(symbol: str, ops = operators): return [o for o in ops if o.symbol == symbol]

infix_operators    = [o for o in operators if o.category == Category.Infix]
prefix_operators   = [o for o in operators if o.category == Category.Prefix]
encloser_operators = [o for o in operators if o.category == Category.Encloser]

# The relationships
make_eq_prec([plus, minus])
make_gt_prec([plus, minus], [mul, neg])

make_gt_prec([mul, div, plus, minus, eq, ne, gt, gte, lt, lte], [ass])

if __name__ == "__main__":
    from pprint import pprint
    pprint(operators, indent=4, depth=3)
