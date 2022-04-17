#pragma once

#include <string>

#include "kol/lexing/ruleset.hpp"
#include "kol/lexing/print.hpp"
#include "kol/lex.hpp"

namespace kol
{
    struct lang
    {
        lexing::ruleset lex_rules;

        constexpr auto load_code(std::string const& code, bool print_lex = false, bool debug_lex = false);
    };

    inline auto bootstrap_lang() -> lang;
}

// Implementations

constexpr auto kol::lang::load_code(std::string const& code, bool print_lex, bool debug_lex)
{
    auto lexed = kol::lex(code, lex_rules, debug_lex);
    if(print_lex && lexed.holds<0>()) kol::lexing::print( lexed.as<0>() );
}

inline auto kol::bootstrap_lang() -> lang
{
    auto ret = lang{.lex_rules = lexing::default_ruleset()};

    return ret;
}
