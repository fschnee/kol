# The ast used by the interpreter, this one is final.

from typing import List, Callable, Any
from dataclasses import dataclass

# Value types.

@dataclass
class KolInt:
    value: int

@dataclass
class KolFloat:
    value: float

@dataclass
class KolFn:
    body: Callable

# Instructions.

# TODO: investigate adding a Lazy wrapper that only evaluates
# when needed (on handle_fn_call).

@dataclass
class Lookup:
    name: str

@dataclass
class Assign:
    name: str
    value: Any

@dataclass
class KolFnCall:
    fn: str | KolFn
    params: List