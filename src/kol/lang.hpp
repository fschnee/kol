#pragma once

#include <string_view>
#include <vector>
#include <span>

// Forward decls.
namespace kol::lexing
{
    template <class> struct context;
    struct discarded;
    struct failed;
}
namespace kol::lexemes { template <class> struct encloser; }

namespace kol
{
    template <class Char>
    struct lang
    {
        using matcher = bool(*)(std::span<Char>);
        using custom_behaviour = variant< lexemes::encloser<Char>, lexing::discarded, lexing::failed >(*)(lexing::context<Char>&);

        struct splitter
        {
            u64 id;

            // When != nullptr calls this function instead of the default
            // when <is_begin> matches.
            // Be careful.
            custom_behaviour on_begin = nullptr;

            /// Debug and user-facing info.

            std::span<Char> name;
            std::span<Char> symbol;

            /// Actual implementation stuff.

            u64 size;

            matcher is_begin;
        };

        struct encloser
        {
            u64 id;

            // When != nullptr calls this function instead of the default
            // when <is_begin> matches.
            // Be careful.
            custom_behaviour on_begin = nullptr;

            /// Debug and user-facing info.

            std::span<Char> name;
            std::span<Char> begin;
            std::span<Char> end;

            // Useful for ignoring sequences that would match <end>.
            // E.g:
            //     {.begin="'", .end="'", .ignored_ending="\\'"}
            //     Will match single-quote strings that end on non-escaped <'> characters.
            std::span<Char> ignored_ending = "";

            /// Actual implemetation stuff.

            matcher is_begin = [](auto){ return false; };
            u64 begin_size   = 0;
            matcher is_end = [](auto){ return false; };
            u64 end_size   = 0;
            matcher is_ignored_ending = [](auto){ return false; };
            u64 ignored_ending_size   = 0;

            // Whether or not to add this encloser to the returning tree.
            // You want to set this to true for stuff that doesn't contribute to
            // the AST, like comments.
            bool is_discarded = false;

            // When true, lexes the inner content.
            // Wanted in function calls, unwanted in strings/comments/macro calls/inline code from other languages.
            // Ignored when <is_discarded> = true.
            bool lex_inner;
        };

        std::vector<splitter> splitters;
        std::vector<encloser> enclosers;

        u64 default_encloser_id;

        constexpr auto get_default_encloser() const -> encloser const*
        {
            for(auto const& e : enclosers)
                if(e.id == default_encloser_id)
                    return &e;
            return nullptr;
        }
    };

    // The default <lang> used by kol, change to extend/make another language.
    template <class Char>
    constexpr auto default_lang() -> lang<Char>
    {
        using namespace std::literals;

        #define KOL_MATCHER(str) [](auto code){ return starts_with(code, str##sv); }

        auto kol = lang<Char>{};

        kol.enclosers.push_back({
            .id = 0_u64,

            .name  = "program",
            .begin = "file begin",
            .end   = "'\\0'",

            .is_end = [](auto code){ return code.size() == 0; },

            .lex_inner = true,
        });
        kol.default_encloser_id = 0_u64;

        auto encloser_id = 1_u64;

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "whitespace-eater",
            .begin = "['\\n', '\\t', '\\v', ' ', '\\r]",
            .end   = "not begin",

            .is_begin   = [](auto code) { return starts_with_any(code, "\n"sv, "\t"sv, "\v"sv, " "sv, "\r"sv); },
            .begin_size = 1,
            .is_end     = [](auto code) { return !starts_with_any(code, "\n"sv, "\t"sv, "\v"sv, " "sv, "\r"sv); },
            .end_size   = 0, // if <is_end> matches we don't want to advance and steal someone else's code.

            .is_discarded = true,
            .lex_inner    = false,
        });

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "comment",
            .begin = "\"//\"",
            .end   = "'\\n'",

            .is_begin   = KOL_MATCHER("//"),
            .begin_size = 2,
            .is_end   = KOL_MATCHER("\n"),
            .end_size = 1,

            .is_discarded = true,
            .lex_inner    = false,
        });

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "multiline comment",
            .begin = "\"/*\"",
            .end   = "\"*/\"",

            .is_begin   = KOL_MATCHER("/*"),
            .begin_size = 2,
            .is_end   = KOL_MATCHER("*/"),
            .end_size = 2,

            .is_discarded = true,
            .lex_inner    = false
        });

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "double-quote str",
            .begin = "'\"'",
            .end   = "'\"'",
            .ignored_ending = "\"\\\"\"",

            .is_begin   = KOL_MATCHER("\""),
            .begin_size = 1,
            .is_end   = KOL_MATCHER("\""),
            .end_size = 1,
            .is_ignored_ending   = KOL_MATCHER("\\\""),
            .ignored_ending_size = 2,

            .lex_inner = false
        });

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "single-quote str",
            .begin = "'''",
            .end   = "'''",
            .ignored_ending = "\"\\'\"",

            .is_begin   = KOL_MATCHER("'"),
            .begin_size = 1,
            .is_end   = KOL_MATCHER("'"),
            .end_size = 1,
            .is_ignored_ending   = KOL_MATCHER("\\'"),
            .ignored_ending_size = 2,

            .lex_inner = false
        });

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "brackets",
            .begin = "'('",
            .end   = "')'",

            .is_begin   = KOL_MATCHER("("),
            .begin_size = 1,
            .is_end   = KOL_MATCHER(")"),
            .end_size = 1,

            .lex_inner = true
        });

        kol.enclosers.push_back({
            .id = encloser_id++,

            .name  = "block",
            .begin = "'{'",
            .end   = "'}'",

            .is_begin   = KOL_MATCHER("{"),
            .begin_size = 1,
            .is_end   = KOL_MATCHER("}"),
            .end_size = 1,

            .lex_inner = true
        });

        auto splitter_id = 0_u64;

        kol.splitters.push_back({
            .id = splitter_id++,
            .name = "expression delimiter",
            .symbol = "';'",
            .size = 1,
            .is_begin = KOL_MATCHER(";")
        });

        kol.splitters.push_back({
            .id = splitter_id++,
            .name = "plus",
            .symbol = "'+'",
            .size = 1,
            .is_begin = KOL_MATCHER("+")
        });

        kol.splitters.push_back({
            .id = splitter_id++,
            .name = "minus",
            .symbol = "'-'",
            .size = 1,
            .is_begin = KOL_MATCHER("-")
        });

        #undef KOL_MATCHER

        return kol;
    }
}
