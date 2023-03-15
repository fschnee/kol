# See https://blog.adamant-lang.org/2019/operator-precedence/

from dataclasses import dataclass, field
from typing import Set, List
from enum import Enum

Associativity = Enum('Associativity', ['Left', 'Right', 'NonAssoc'])
Precedence    = Enum('Precedence', ['Equal', 'Lower', 'Higher', 'NoPrecedence'])
Category      = Enum('Category', ['Prefix', 'Infix', 'Encloser'])

@dataclass
class Operator:
    name: str
    symbol: str

    category: Category = Category.Infix
    assoc: Associativity = Associativity.Left # TODO: assure operators of equal precedence have the same associativity.

    eq_prec: List['Operator'] = field(default_factory=lambda: [])
    gt_prec: List['Operator'] = field(default_factory=lambda: [])

    opening: 'Operator' = None
    closing: 'Operator' = None

    def precedence_to(self, op):
        if op in self.eq_prec:   return Precedence.Equal
        elif self in op.gt_prec: return Precedence.Higher
        elif op in self.gt_prec: return Precedence.Lower
        else:                    return Precedence.NoPrecedence

    def __repr__(self): return f"Op({self.name}: '{self.symbol}')"

# Precedence stuff
def make_eq_prec(ops: List):
    for o in ops:
        for o2 in ops:
            if o2 not in o.eq_prec: o.eq_prec.append(o2)

def make_gt_prec(ops: List, gt: List):
    for o in ops:
        for o2 in gt:
            if o2 not in o.gt_prec: o.gt_prec.append(o2)

# The operators themselves
mul = Operator('mul', '*')
div = Operator('div', '/')
plus = Operator('plus', '+')
minus = Operator('minus', '-')
neg = Operator('neg', '-', Category.Prefix)
ass = Operator('ass', '=')

lparen = Operator('lparen', '(', Category.Encloser)
rparen = Operator('rparen', ')', Category.Encloser)
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
