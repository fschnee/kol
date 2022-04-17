#pragma once

#include <string_view>
#include <string>

namespace kol::strutils
{
    inline auto replace_escape_sequences(std::string_view) -> std::string;
}

inline auto kol::strutils::replace_escape_sequences(std::string_view str) -> std::string
{
    auto out = std::string(str);
    auto pos = out.npos;

    #define KOL_STRUTILS_ESCAPE_HELPER(needle, replacer) \
        while((pos = out.find(needle)) != out.npos) \
            out = out.replace(pos, 1, replacer, 2);

    KOL_STRUTILS_ESCAPE_HELPER('\a', "\\a")
    KOL_STRUTILS_ESCAPE_HELPER('\b', "\\b")
    KOL_STRUTILS_ESCAPE_HELPER('\t', "\\t")
    KOL_STRUTILS_ESCAPE_HELPER('\n', "\\n")
    KOL_STRUTILS_ESCAPE_HELPER('\v', "\\v")
    KOL_STRUTILS_ESCAPE_HELPER('\f', "\\f")
    KOL_STRUTILS_ESCAPE_HELPER('\r', "\\r")

    #undef KOL_STRUTILS_ESCAPE_HELPER

    return out;
}
