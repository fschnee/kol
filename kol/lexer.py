import kol.tokenizer as tok
import kol.defs      as defs

class Glyph:
    def __init__(self, text): self.text = text
    def __repr__(self): return self.text
class Text:
    def __init__(self, text): self.text = text.strip()
    def __repr__(self): return f"\"{self.text}\""

def lex(text):
    text_stack = []
    for t in tok.tokenize(text):
        if t in defs.glyphs:
            if len(text_stack):
                yield Text(" ".join(text_stack))
                text_stack = []
            yield Glyph(t)
        else: text_stack.append(t)

    if len(text_stack): yield Text(" ".join(text_stack))

if __name__ == "__main__":
    from sys import argv
    with open(argv[1]) as f: print( list( lex(f.read()) ))

