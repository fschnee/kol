import kol.defs as defs

def ysplit(pred, it, post = lambda x: x, acceptor = lambda x: True, _split = 0, _offset = 0):
    "(Kind of) a yielding version of str.split"

    while True:
        if len(it) == 0: break

        if not (pred(it[:_split]) or _split == len(it)):
            _split, _offset = _split + 1, 0
            continue

        if acceptor( it[:_split] ):
            _offset, toks = post( it[:_split] )
            for tok in toks: yield tok

        _split, _offset, it = 0, 0, it[_split + _offset:]

def split_and_keep(s, sep):
    idx = s.find(sep)
    if s == '':     return []
    elif idx == -1: return [s]
    elif idx == 0:  return [sep, *split_and_keep(s[idx + len(sep):], sep)]
    else:           return [s[0:idx], sep, *split_and_keep(s[idx + len(sep):], sep)]

def flatten(l): return [item for sublist in l for item in sublist]

def glyphsplit(s, glyphs = list(sorted(defs.glyphs, key=len, reverse=True))): return glyphsplit_impl([s], glyphs, glyphs)
def glyphsplit_impl(strs, remaining_glyphs, glyphs):
    if len(remaining_glyphs) == 0: return strs
    return glyphsplit_impl(
        flatten([(split_and_keep(s, remaining_glyphs[0]) if s not in glyphs else [s]) for s in strs]),
        remaining_glyphs[1:],
        glyphs
    )

def should_split(s):
    if s.startswith('//'): return s.endswith('\n')
    elif s.startswith(defs.glyphs): return not s.endswith(defs.glyphs)
    elif s.endswith(defs.glyphs): return True
    else: return s.endswith(defs.whitespace)

def post_backtracker(s):
    parts = glyphsplit(s)
    if len(parts) == 1: return 0, parts
    elif parts[0] in defs.glyphs or parts[-1] in defs.glyphs: return -len(''.join(parts[1:])), [parts[0]]
    else: return len(s.strip()) - len(s), [s.strip()]

def should_accept(s): return not s.startswith('//') and not s in defs.whitespace
def tokenize(data): yield from ysplit(should_split, data, post_backtracker, should_accept)

if __name__ == "__main__":
    from sys import argv
    with open(argv[1]) as f: print( list( tokenize(f.read()) ))
