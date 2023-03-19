# See https://blog.adamant-lang.org/2019/operator-precedence/

from dataclasses import dataclass, field
from typing import Set, List, Callable
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
