import kol.operators as ops
import kol.defs  as defs
import kol.lexer as lex

from dataclasses import dataclass, field
from itertools import chain
from typing import List, Callable, Any

@dataclass
class GeneratorWrapper:
    gen: Callable = None
    is_done: bool = False

    def next(self):
        try: return next(self.gen)
        except StopIteration as e:
            self.is_done = True
            return e

    def prepend(self, el): self.prepend_many([el])
    def prepend_many(self, els):
        self.is_done = False
        self.gen = chain(els, self.gen)

    def peek(self):
        n = self.next()
        self.prepend(n)
        return n

@dataclass
class UnwindableMatch:
    _type: Any
    _unwind_order: List[str] = field(default_factory = lambda: [])
    _fields: List['UnwindableMatch'] = field(default_factory = lambda: [])

    def unwind(self, g: GeneratorWrapper, r: List['Rule']):
        for v in map(lambda att: getattr(self, att), self._unwind_order):
            if type(v) is UnwindableMatch: v.unwind(g, r)
            else:                          g.prepend(v)

@dataclass
class Rule:
    name: str
    branches: None | List
    # In case you need more control than branch matching.
    detector: None | Callable[[GeneratorWrapper, List['Rule']], UnwindableMatch | None] = None

@dataclass
class Branch:
    name: str
    arms: List

@dataclass
class Arm:
    name: str
    value: str | Rule

# Enclosers are special since they are 2 (different) symbols.
default_rules_str = """
expr' === unop ==> unop expr:::expr' ||| ident ==> ident ||| """ + " ||| ".join([f"encloser-{o.name} ==> opener:::encloser-{o.name}-opener expr closer:::encloser-{o.name}-closer" for o in ops.encloser_operators if o.opening is o]) + """
expr  === binop ==> lhs:::expr' binop rhs:::expr ||| simple-expr ==> expr:::expr'
stmt  === expr-stmt ==> expr endstmt
stmts === multiple ==> stmt stmts ||| single ==> stmt
"""

extra_rules = []

def rule_from_string(line: str) -> Rule:
    rule_name, branches_str = line.split('===')

    branches = []
    for branch in branches_str.split('|||'):
        branchname, branch = branch.split('==>')
        branchname = branchname.strip()
        if branch == None: branch = branchname

        leafs = map(str.strip, branch.split())

        branch = Branch(branchname, [])
        for leaf in leafs:
            try:               name, rule = leaf.split(':::')
            except ValueError: name, rule = leaf, leaf
            branch.arms.append(Arm(name, rule))

        branches.append(branch)

    return Rule(rule_name.strip(), branches)

def create_rules(lines: str, extra_rules: List[Rule] = []) -> List[Rule]:
    # Create all the rules individually.
    rules = list( map( rule_from_string, filter( lambda x: x != '', lines.splitlines() ) ) )
    rules = [*rules, *extra_rules]

    # Then resolve all the branches with the correct production rules.
    for rule in rules:
        if rule.branches is None: continue

        for branch in rule.branches:
            for arm in branch.arms:
                r = list( filter(lambda x: x.name == arm.value, rules) )
                if len(r): arm.value = r[0]
                # TODO: else error
    return rules

def generic_single_detector(unwind_name, fieldname, cond):
    def detector(g, r):
        el = g.next()
        if g.is_done: return

        if cond(el):
            match = UnwindableMatch(unwind_name)
            setattr(match, fieldname, el)
            match._fields.append(el)
            match._unwind_order = [fieldname]
            return match
        else: g.prepend(el)

    return detector

extra_rules += [
    Rule('endstmt', None, generic_single_detector('endstmt', 'glyph', lambda o: o.text == defs.endstmt)),
    Rule('unop',    None, generic_single_detector('unop',    'op',    lambda o: o.text in [o.symbol for o in ops.prefix_operators])),
    Rule('binop',   None, generic_single_detector('binop',   'op',    lambda o: o.text in [o.symbol for o in ops.infix_operators])),
    Rule('ident',   None, generic_single_detector('ident',   'ident', lambda i: type(i) is lex.Text)),
]

for o in ops.encloser_operators:
    if o.opening is not o: continue

    extra_rules += [
        Rule(f'encloser-{o.name}-opener', None, generic_single_detector('encloser', 'op', lambda _o: _o.text == o.opening.symbol)),
        Rule(f'encloser-{o.name}-closer', None, generic_single_detector('encloser', 'op', lambda _o: _o.text == o.closing.symbol)),
    ]

default_rules = create_rules(default_rules_str, extra_rules)

def parse_impl(g: GeneratorWrapper, rules: List[Rule], r: Rule, depth=0, debug = False) -> UnwindableMatch | None:
    if g.is_done: return

    if r.detector is not None:
        match = r.detector(g, rules)
        if debug: print(' ' * depth, r.name + '(detector)', match != None)
        return match

    if debug: print(' ' * depth, r.name, [branch.name for branch in r.branches])

    # Otherwise, match using the branches.
    for branch in r.branches:
        if debug: print(' ' * depth, r.name + ':' + branch.name + '(stepping in)', [a.name for a in branch.arms])
        arms = []
        success = True

        for a in branch.arms:
            _a = parse_impl(g, rules, a.value, depth + 4, debug)
            if _a is None: # Cleanup if not matched
                success = False
                break
            else: arms.append((a.name, _a))

        if success:
            if debug: print(' ' * depth, r.name + ':' + branch.name + '(success)')
            match = UnwindableMatch(r.name + ':' + branch.name)
            for a in arms:
                setattr(match, a[0], a[1])
                match._fields.append(a[1])
            match._unwind_order = list(reversed([a[0] for a in arms]))
            return match
        else:
            if debug: print(' ' * depth, r.name + ':' + branch.name + '(fail)')
            for (_, a) in reversed(arms): a.unwind(g, rules)
            arms = None


def parse(text: str, rules: List[Rule] = default_rules, start_rule_name: str = 'stmts', debug = False):
    g = GeneratorWrapper(lex.lex(text))
    return parse_impl(g, rules, [r for r in rules if r.name == start_rule_name][0], debug = debug), g

if __name__ == "__main__":
    from pprint import pprint
    from sys import argv

    print(default_rules_str)
    with open(argv[1]) as f:
        res, g = parse(f.read(), debug = True)
        pprint(res, indent=4)