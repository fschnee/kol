import kol.operators as ops

whitespace = (' ', '\n', '\r', '\t', '\f')
endstmt    = ';'
glyphs     = tuple(['=>', '...', endstmt, *[o.symbol for o in ops.operators]])