#pragma once

#include "kol/utils/strutils.hpp"
#include "kol/utils/variant.hpp"
#include "kol/utils/aliases.hpp"
#include "kol/lexing/ruleset.hpp"

#include <string_view>
#include <iostream> // Used when ctx.is_debug = true.
#include <vector>
#include <string>

// Forward decls.
namespace kol::lexemes
{
    struct splitter;
    struct blob;
    struct encloser;
}

namespace kol
{
    using lexeme = variant<
        lexemes::splitter,
        lexemes::blob,
        lexemes::encloser
    >;

    namespace lexemes
    {
        struct splitter
        {
            lexing::ruleset::splitter const* splitter;
        };

        struct blob
        {
            std::string code;
        };

        struct encloser
        {
            using sublexemes = std::vector<lexeme>;  // When <punct.lex_inner> = true.
            using subcode    = std::string;          // When <punct.lex_inner> = false.

            lexing::ruleset::encloser const* encloser;
            variant<sublexemes, subcode> inner;
        };
    }

    namespace lexing
    {
        struct context
        {
            std::string_view const code;
            ruleset const& rules;

            std::string_view remaining;
            std::vector< decltype(ruleset::encloser::id) > enclosing_stack;

            u64 index;
            u64 line;
            u64 column;

            bool debug;

            // Returns true if <remaining> is exhausted.
            constexpr auto advance() -> bool;
            // Returns how much was actually advanced.
            constexpr auto advance(u64 amount) -> u64;
        };

        // Just tags to represent some status.
        struct discarded {};
        struct failed {}; // TODO: implement

        constexpr auto lex_enclosing(context& ctx) -> variant< lexemes::encloser, discarded, failed >;
    }

    inline auto lex(
        std::string_view code,
        lexing::ruleset& lex_rules,
        bool debug = false
    ) -> variant< lexemes::encloser, lexing::failed >;
}

// Implementations.

constexpr auto kol::lexing::context::advance() -> bool
{
    if(remaining.size() == 0) return false;
    remaining = remaining.substr(1);

    auto newline = remaining.starts_with('\n');
    ++index;
    line  += newline;
    column = column * !newline + 1;

    return true;
}

constexpr auto kol::lexing::context::advance(u64 amount) -> u64
{
    auto advanced = 0_u64;
    while(amount) { --amount; if(!advance()) return advanced; ++advanced; }
    return advanced;
}

inline auto kol::lex(std::string_view code, lexing::ruleset& lex_rules, bool debug)
    -> variant< lexemes::encloser, lexing::failed >
{
    auto ctx = lexing::context
    {
        .code = code,
        .rules = lex_rules,
        .remaining = code,
        .enclosing_stack = { lex_rules.default_encloser_id },
        .index = 0,
        .line = 1,
        .column = 1,
        .debug = debug
    };

    return lexing::lex_enclosing(ctx).drop< lexing::discarded >();
}

constexpr auto kol::lexing::lex_enclosing(context& ctx)
    -> variant< lexemes::encloser, discarded, failed >
{
    auto const& me = *ctx.rules.get_encloser( ctx.enclosing_stack.back() );

    auto debug = [&](auto... args)
    {
        if(!ctx.debug) return;
        auto const indentation = std::string((ctx.enclosing_stack.size() - 1) * 4, ' ');
        std::cout << indentation << me.name << ' ';
        (std::cout << ... << args) << std::flush;
    };

    KOL_DONT_FORGET( ctx.enclosing_stack.pop_back() );

    using sublexemes = lexemes::encloser::sublexemes;
    using subcode    = lexemes::encloser::subcode;

    auto ret = lexemes::encloser{ .encloser = &me };
    if(!me.is_discarded && me.lex_inner) ret.inner = sublexemes{};
    else if(!me.is_discarded)            ret.inner = subcode{};

    /* Stuff to automate boilerplate. */

    auto const make_nicely_printable = [](auto code) -> std::string
    {
        if(code.size() == 0) return "\\0";
        return strutils::replace_escape_sequences(code.substr(0, 60)).substr(0, 60);
    };

    auto const push_encloser = [&](lexemes::encloser&& e)
    {
        debug("+ pushing encloser <", e.encloser->name, ">\n");
        ret.inner.as<sublexemes>().push_back( KOL_MOV(e) );
    };
    auto const push_splitter = [&](auto s)
    {
        debug("+ pushing splitter <", s->name, ">\n");
        ret.inner.as<sublexemes>().push_back( lexemes::splitter{ s } );
    };
    auto const push_blob_or_subcode = [&](std::string_view data)
    {
        if(ctx.debug) debug("+ pushing blob_or_subcode <", make_nicely_printable(data), ">\n");
        ret.inner
            .on<sublexemes>([&](auto& l){ l.push_back( lexemes::blob{ std::string{data} }); })
            .on<subcode>([&](auto& c){ c = data; });
    };

    /* Stuff for checking for matches. */

    auto const consider_matches = !me.is_discarded && me.lex_inner;

    ruleset::splitter const* splitter_match = nullptr;
    ruleset::encloser const* encloser_match = nullptr;
    auto const try_match_splitter =  [&]
    {
        for(auto& s : ctx.rules.splitters)
            if(s.is_begin(ctx.remaining)) { splitter_match = &s; return true; }
        return false;
    };
    auto const try_match_encloser =  [&]
    {
        for(auto& e : ctx.rules.enclosers)
            if(e.is_begin(ctx.remaining)) { encloser_match = &e; return true; }
        return false;
    };

    auto const sublexemes_size = [&]
    {
        auto size = 0;
        ret.inner.on<sublexemes>([&](auto& ls){ size = ls.size(); });
        return size;
    };

    /* Some state to keep track of during our lexing loop. */

    // Blob accumulator (sounds funny).
    auto acc = ctx.remaining.data();
    auto acc_len = 0_u64;
    // Whether or not to reset out accumulator.
    auto reset_acc = true;
    // Are we done (found is_end()) ?
    auto done = false;
    // Did something go bad ?
    auto end_prematurely = false;
    // How much to advance the <ctx.remaining>, is reset to 0 at the beggining of each loop.
    auto advance = 0_u64;

    /* What to do when we get a match. */

    auto do_splitter_match = [&]
    {
        if(acc_len) push_blob_or_subcode({acc, acc_len});
        reset_acc = true;

        push_splitter(splitter_match);
        advance = splitter_match->size;
    };
    auto do_encloser_match = [&]
    {
        if(acc_len) push_blob_or_subcode({acc, acc_len});
        reset_acc = true;

        ctx.enclosing_stack.push_back(encloser_match->id);
        end_prematurely = ctx.advance(encloser_match->begin_size) != encloser_match->begin_size;
        lex_enclosing(ctx)
            .on< lexemes::encloser >([&](auto& e){ push_encloser(KOL_MOV(e)); })
            .on< discarded >([&](auto&){ debug("- <", encloser_match->name, "> discarded\n"); }) // no-op.
            .on< failed >([&](auto&){ end_prematurely = true; });
    };

    /* The actual lexing loop. */

    while(!done)
    {
        advance = 0;

        if(reset_acc)
        {
            acc       = ctx.remaining.data();
            acc_len   = 0;
            reset_acc = false;
        }

        // Avoid allocating strings if we don't need to (make_nicely_printable allocates).
        if(ctx.debug)
            debug(sublexemes_size(), ": <", make_nicely_printable(ctx.remaining), ">\n");

        if(consider_matches && try_match_splitter())
        { do_splitter_match(); }
        else if(consider_matches && try_match_encloser())
        { do_encloser_match(); }
        else if(me.is_ignored_ending(ctx.remaining))
        { advance = me.ignored_ending_size; }
        else if(me.is_end(ctx.remaining))
        {
            done = true;
            debug("= matched .is_end(...), ending\n");
            advance = me.end_size;
        }
        else { advance = 1; }

        if(end_prematurely || ctx.advance(advance) != advance) break;

        if(done && !me.is_discarded && acc_len) push_blob_or_subcode({acc, acc_len});
        else acc_len += advance;
    }

    if(!done || end_prematurely) return failed{};
    else if(me.is_discarded)     return discarded{};
    else                         return ret;
}
