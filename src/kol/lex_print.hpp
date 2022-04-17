#pragma once

#include "kol/utils/aliases.hpp"
#include "kol/lex.hpp"

#include <vector>
#include <type_traits>

namespace kol::lexing
{
    auto print(const lexemes::splitter&, u64 indent_size = 4, u64 indent = 0);
    auto print(const lexemes::blob&, u64 indent_size = 4, u64 indent = 0);
    auto print(const lexemes::encloser&, u64 indent_size = 4, u64 indent = 0);
}

auto kol::lexing::print(const lexemes::splitter& s, u64 indent_size, u64 indent)
{
    auto const do_indent = [&](){ for(auto i = 0_u64; i < indent * indent_size; ++i) std::cout << ' '; };

    do_indent();
    std::cout
        << "splitter(name = " << s.splitter->name
        << ", symbol = " << s.splitter->symbol
        << ")\n";
}

auto kol::lexing::print(const lexemes::blob& b, u64 indent_size, u64 indent)
{
    auto const do_indent = [&](){ for(auto i = 0_u64; i < indent * indent_size; ++i) std::cout << ' '; };

    do_indent();
    std::cout << "blob<" << b.code << ">\n";
}

auto kol::lexing::print(const lexemes::encloser& e, u64 indent_size, u64 indent)
{
    auto const do_indent = [&](){ for(auto i = 0_u64; i < indent * indent_size; ++i) std::cout << ' '; };

    do_indent();
    std::cout
        << "encloser(id = " << e.encloser->id
        << ", name = " << e.encloser->name
        << ", begin = " << e.encloser->begin
        << ", end = " << e.encloser->end
        << ", lex_inner = " << e.encloser->lex_inner
        << ")\n";

    if(e.inner.holds< lexemes::encloser::subcode >())
    {
        indent = indent + 1;
        do_indent();
        std::cout << '<' << e.inner.as< lexemes::encloser::subcode >() << ">\n";
        return;
    }

    auto& sub = e.inner.as< lexemes::encloser::sublexemes >();
    for(auto const& sublexeme : sub) sublexeme
        .on<lexemes::splitter>([&](auto& s){ print(s, indent_size, indent+1); })
        .on<lexemes::blob>    ([&](auto& b){ print(b, indent_size, indent+1); })
        .on<lexemes::encloser>([&](auto& e){ print(e, indent_size, indent+1); });
}
