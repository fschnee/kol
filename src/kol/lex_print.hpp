#pragma once

#include "kol/utils/aliases.hpp"
#include "kol/lex.hpp"

#include <vector>
#include <type_traits>

namespace kol::lexing
{
    template <typename Char>
    auto print(const std::vector<lexeme<Char>>&, u64 indent_size = 4, u64 indent = 0);
}

template <typename Char>
auto kol::lexing::print(const std::vector<lexeme<Char>>& lexemes, u64 indent_size, u64 indent)
{

    auto const do_indent = [&](){ for(auto i = 0; i < indent; ++i) std::cout << ' '; };

    std::cout << "[\n";
    indent += indent_size;

    // for(auto& lexeme : lexemes) std::visit([&](auto&& l) {
    //     using T = std::decay_t< decltype(l) >;

    //     do_indent();

    //     if constexpr(std::is_same_v<T, typename kol::lexeme<Char>::splitting_punct_t>)
    //         std::cout << "spt: " << l.punct.id << " with symbol \"" << l.punct.symbol << "\"\n";

    //     return;

    // }, lexeme.data);

    std::cout << ']';
}
