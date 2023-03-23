import kol.operators as ops
import kol.defs  as defs
import kol.lexer as lex

from dataclasses import dataclass, field
from typing import List, Callable, Any

@dataclass
class GeneratorWrapper:
    gen: Callable = None
    is_done: bool = False

    def next(self):
        try: 
            if type(self.gen) is list:
                ret = self.gen.pop(0)
                if len(self.gen) == 1: self.gen = self.gen[0]
                return ret 
            else: return next(self.gen)
        except StopIteration as e:
            self.is_done = True
            return e

    def prepend(self, el): self.prepend_many([el])
    def prepend_many(self, els):
        self.is_done = False
        if type(self.gen) is list: self.gen = els + self.gen
        else: self.gen = els + [self.gen]

    def peek(self):
        n = self.next()
        self.prepend(n)
        return n

@dataclass
class UnwindableMatch:
    _type: Any
    _unwind_order: List[str] = field(default_factory = lambda: [])
    _fieldnames: List[str] = field(default_factory = lambda: [])
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
endstmts === multiple ==> endstmt endstmts ||| single ==> endstmt

stmt  === block    ==> { stmts } endstmt   ||| empty-block ==> { }     ||| expr-stmt ==> expr
stmts === multiple ==> stmt endstmts stmts ||| last2 ==> stmt endstmts ||| last ==> stmt

expr' === ifexpr ==> ifexpr ||| unop ==> unop expr:::expr' ||| fncall-noargs ==> ident ( ) ||| fncall ==> ident ( fncallargs ) ||| anon-fncall ==> ( fncallargs ) ||| anon-fncall-noargs ==> ( ) ||| fndef ==> fndef ||| ident ==> ident
expr  === binop  ==> partial:::binopleftpartial rhs:::expr ||| simple-expr ==> expr:::expr'

ident === multiple ==> _ident ident ||| single ==> _ident

binoprightpartial === partial  ==>             binop rhs:::expr
binopleftpartial  === partial  ==> lhs:::expr' binop
binopleftpartials === multiple ==> first:::binopleftpartial rest:::binopleftpartials ||| single ==> first:::binopleftpartial

fncallargs === multiple  ==> first:::expr endstmt rest:::fncallargs ||| single ==> expr 
fndef      === with-args ==> [ fncallargs ] { stmts }               ||| without-args ==> [ ] { stmts } ||| minimal ==> { stmts }

ifexpr     === regular  ==> if arms:::ifarms end           ||| rpartial-named ==> if expr => varname:::ident ... arms:::ifrparms end ||| lpartial-named ==> if binopleftpartials => varname:::ident ... arms:::iflparms end ||| rpartial ==> if expr ... arms:::ifrparms end ||| lpartial ==> if binopleftpartials ... arms:::iflparms end
iflparm    === ellipsis ==> ... => { stmts }               ||| expr     ==> ... expr => { stmts } ||| rpartial ==> ... binoprightpartial => { stmts } ||| lp-expr ==> expr => { stmts }
ifrparm    === ellipsis ==> ... => { stmts }               ||| expr     ==> ... expr => { stmts } ||| rpartial ==>     binoprightpartial => { stmts }
ifarm      === ellipsis ==> ... => { stmts }               ||| expr     ==>     expr => { stmts }
ifarms     === multiple ==> arm:::ifarm   rest:::ifarms    ||| single   ==> arm:::ifarm
iflparms   === multiple ==> arm:::iflparm rest:::iflparms  ||| single   ==> arm:::iflparm
ifrparms   === multiple ==> arm:::ifrparm rest:::ifrparms  ||| single   ==> arm:::ifrparm
"""

# Rules unexpressable using the above syntax.
# Basically the most fundamental rules go here.
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

def detector(g, r, unwind_name, fieldname, cond):
    el = g.next()
    if g.is_done: return

    if cond(el):
        match = UnwindableMatch(unwind_name)
        setattr(match, fieldname, el)
        match._fieldnames.append(fieldname)
        match._fields.append(el)
        match._unwind_order = [fieldname]
        return match
    else: g.prepend(el)

def generic_single_detector(unwind_name, fieldname, cond):
    return lambda g, r: detector(g, r, unwind_name, fieldname, cond)

extra_rules += [
    Rule('endstmt', None, generic_single_detector('endstmt', 'glyph', lambda o: o.text == defs.endstmt)),
    Rule('unop',    None, generic_single_detector('unop',    'op',    lambda o: o.text in [o.symbol for o in ops.prefix_operators])),
    Rule('binop',   None, generic_single_detector('binop',   'op',    lambda o: o.text in [o.symbol for o in ops.infix_operators])),
    Rule('_ident',  None, generic_single_detector('ident',   'ident', lambda i: type(i) is lex.Text)),
]

for o in ops.encloser_operators:
    if o.opening is not o: continue

    extra_rules += [
        Rule(f'encloser-{o.name}-opener', None, generic_single_detector('encloser', 'op', lambda _o, o=o: _o.text == o.opening.symbol)),
        Rule(o.opening.symbol,            None, generic_single_detector('encloser', 'op', lambda _o, o=o: _o.text == o.opening.symbol)),
        Rule(f'encloser-{o.name}-closer', None, generic_single_detector('encloser', 'op', lambda _o, o=o: _o.text == o.closing.symbol)),
        Rule(o.closing.symbol,            None, generic_single_detector('encloser', 'op', lambda _o, o=o: _o.text == o.closing.symbol)),
    ]

extra_rules += [
    Rule('...', None, generic_single_detector('ellipsis',  'op',  lambda _o: _o.text == '...')),
    Rule('=>',  None, generic_single_detector('fat-arrow', 'op',  lambda _o: _o.text == '=>')),
    Rule('if',  None, generic_single_detector('if',        'if',  lambda _o: _o.text == 'if')),
    Rule('end', None, generic_single_detector('end',       'end', lambda _o: _o.text == 'end')),
]

default_rules = create_rules(default_rules_str, extra_rules)

def parse_impl(g: GeneratorWrapper, rules: List[Rule], r: Rule, depth = 0, debug = False) -> UnwindableMatch | None:
    if g.is_done: return

    if r.detector is not None:
        match = r.detector(g, rules)
        if debug: print(' ' * depth + r.name + '(detector)', match != None, g)
        return match

    if debug: print(' ' * depth + r.name, [branch.name for branch in r.branches], g)

    # Otherwise, match using the branches.
    for branch in r.branches:
        if debug: print(' ' * depth + r.name + ':' + branch.name + '(stepping in)', [a.name for a in branch.arms], g)
        arms = []
        success = True

        for a in branch.arms:
            _a = parse_impl(g, rules, a.value, depth + 4, debug)
            if _a is None: # Cleanup if not matched
                success = False
                break
            else: arms.append((a.name, _a))

        if success:
            if debug: print(' ' * depth + r.name + ':' + branch.name + '(success)', g)
            match = UnwindableMatch(r.name + ':' + branch.name)
            for a in arms:
                setattr(match, a[0], a[1])
                match._fieldnames.append(a[0])
                match._fields.append(a[1])
            match._unwind_order = list(reversed([a[0] for a in arms]))
            return match
        else:
            if debug: print(' ' * depth + r.name + ':' + branch.name + '(fail)', g)
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