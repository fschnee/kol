#pragma once

#include <string>

#include "kol/lex_print.hpp"
#include "kol/lexdata.hpp"
#include "kol/lex.hpp"

namespace kol
{
    struct lang
    {
        lexing::data lex_rules;

        constexpr auto load_code(std::string const& code, bool print_lex = false, bool debug_lex = false);
    };

    inline auto make_lang() -> lang;
}

// Implementations

constexpr auto kol::lang::load_code(std::string const& code, bool print_lex, bool debug_lex)
{
    auto lexed = kol::lex(code, lex_rules, debug_lex);
    if(print_lex && lexed.holds<0>()) kol::lexing::print( lexed.as<0>() );
}

inline auto kol::make_lang() -> lang
{
    auto ret = lang{.lex_rules = lexing::make_data()};

    return ret;
}
