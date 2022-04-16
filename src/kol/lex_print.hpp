#pragma once

#include "kol/utils/aliases.hpp"
#include "kol/lex.hpp"

#include <vector>
#include <type_traits>

namespace kol::lexing
{
    template <typename Char>
    auto print(const lexemes::splitter<Char>&, u64 indent_size = 4, u64 indent = 0);
    template <typename Char>
    auto print(const lexemes::blob<Char>&, u64 indent_size = 4, u64 indent = 0);
    template <typename Char>
    auto print(const lexemes::encloser<Char>&, u64 indent_size = 4, u64 indent = 0);
}

template <typename Char>
auto kol::lexing::print(const lexemes::splitter<Char>& s, u64 indent_size, u64 indent)
{
    auto const do_indent = [&](){ for(auto i = 0_u64; i < indent * indent_size; ++i) std::cout << ' '; };
    auto const to_sv = [](auto span){ return std::string_view{span.begin(), span.end()}; };
    do_indent();
    std::cout
        << "splitter(name = " << to_sv(s.splitter->name)
        << ", symbol = " << to_sv(s.splitter->symbol)
        << ")\n";
}

template <typename Char>
auto kol::lexing::print(const lexemes::blob<Char>& b, u64 indent_size, u64 indent)
{
    auto const do_indent = [&](){ for(auto i = 0_u64; i < indent * indent_size; ++i) std::cout << ' '; };
    auto const to_sv = [](auto span){ return std::string_view{span.begin(), span.end()}; };

    do_indent();
    std::cout << "blob<" << to_sv(b.code) << ">\n";
}

template <typename Char>
auto kol::lexing::print(const lexemes::encloser<Char>& e, u64 indent_size, u64 indent)
{

    auto const do_indent = [&](){ for(auto i = 0_u64; i < indent * indent_size; ++i) std::cout << ' '; };
    auto const to_sv = [](auto span){ return std::string_view{span.begin(), span.end()}; };

    do_indent();
    std::cout
        << "encloser(id = " << e.encloser->id
        << ", name = " << to_sv(e.encloser->name)
        << ", begin = " << to_sv(e.encloser->begin)
        << ", end = " << to_sv(e.encloser->end)
        << ", lex_inner = " << e.encloser->lex_inner
        << ")\n";

    using subcode    = typename lexemes::encloser<Char>::subcode;
    if(e.inner.template holds<subcode>())
    {
        indent = indent + 1;
        do_indent();
        std::cout << '<' << to_sv(e.inner.template as<subcode>()) << ">\n";
        return;
    }

    using splitter   = lexemes::splitter<Char>;
    using blob       = lexemes::blob<Char>;
    using encloser   = lexemes::encloser<Char>;
    using sublexemes = typename lexemes::encloser<Char>::sublexemes;
    auto& sub = e.inner.template as<sublexemes>();
    for(auto const& sublexeme : sub) sublexeme
        .template on<splitter>([&](auto& s){ print(s, indent_size, indent+1); })
        .template on<blob>    ([&](auto& b){ print(b, indent_size, indent+1); })
        .template on<encloser>([&](auto& e){ print(e, indent_size, indent+1); });
}
