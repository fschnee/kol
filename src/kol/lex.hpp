#pragma once

#include "kol/utils/variant.hpp"
#include "kol/utils/aliases.hpp"
#include "kol/lang.hpp"

#include <iostream> // Used when ctx.is_debug = true.
#include <vector>
#include <span>

// Forward decls.
namespace kol::lexemes
{
    template <class> struct splitter;
    template <class> struct blob;
    template <class> struct encloser;
}

namespace kol
{
    template <typename Char>
    using lexeme = variant<
        lexemes::splitter<Char>,
        lexemes::blob<Char>,
        lexemes::encloser<Char>
    >;

    namespace lexemes
    {
        template <class Char>
        struct splitter
        {
            typename lang<Char>::splitter const* splitter;
        };

        template <class Char>
        struct blob
        {
            std::span<Char> code;
        };

        template <class Char>
        struct encloser
        {
            using sublexemes = std::vector<lexeme<Char>>;  // When <punct.lex_inner> = true.
            using subcode    = std::span<Char>;            // When <punct.lex_inner> = false.

            typename lang<Char>::encloser const* encloser;
            variant<sublexemes, subcode> inner;
        };
    }

    namespace lexing
    {
        template <class Char>
        struct context
        {
            std::span<Char> const code;
            lang<Char> const& target_lang;

            std::span<Char> remaining;
            std::vector< typename lang<Char>::encloser const* > enclosing_stack;

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

        template <class Char>
        constexpr auto lex_enclosing(context<Char>& ctx) -> variant< lexemes::encloser<Char>, discarded, failed >;
    }

    template <class Char>
    constexpr auto lex(
        std::span<Char> const code,
        lang<Char> const& lang, // Must stay as live as long as the lexing return.
        bool debug = false
    ) -> variant< lexemes::encloser<Char>, lexing::failed >;
}

// Implementations.

template <class Char>
constexpr auto kol::lexing::context<Char>::advance() -> bool
{
    if(remaining.size() == 0) return false;
    remaining = remaining.subspan(1);

    auto newline = starts_with(remaining, std::string_view{"\n"});
    ++index;
    line  += newline;
    column = column * !newline + 1;

    return true;
}

template <class Char>
constexpr auto kol::lexing::context<Char>::advance(u64 amount) -> u64
{
    auto advanced = 0_u64;
    while(amount) { --amount; if(!advance()) return advanced; ++advanced; }
    return advanced;
}

template <class Char>
constexpr auto kol::lex(std::span<Char> const code, lang<Char> const& lang, bool debug)
    -> variant< lexemes::encloser<Char>, lexing::failed >
{
    auto ctx = lexing::context<Char>
    {
        .code = code,
        .target_lang = lang,
        .remaining = code,
        .enclosing_stack = { lang.get_default_encloser() },
        .index = 0,
        .line = 1,
        .column = 1,
        .debug = debug
    };

    auto ret = variant< lexemes::encloser<Char>, lexing::failed >{};
    lexing::lex_enclosing(ctx)
        .template on< lexemes::encloser<Char> >([&](auto l){ ret = KOL_MOV(l); })
        .template on< lexing::failed >([&](auto f){ ret = KOL_MOV(f); });
    return ret;
}

template <class Char>
constexpr auto kol::lexing::lex_enclosing(context<Char>& ctx)
    -> variant< lexemes::encloser<Char>, discarded, failed >
{
    auto const& me = *ctx.enclosing_stack.back();

    // If custom_behaviour is specified we defer to it.
    if(me.on_begin) return me.on_begin(ctx);

    auto debug = [&](auto... args)
    {
        if(!ctx.debug) return;
        auto const indentation = std::string((ctx.enclosing_stack.size() - 1) * 4, ' ');
        std::cout << indentation << me.name.data() << ' ';
        (std::cout << ... << args) << std::flush;
    };

    KOL_DONT_FORGET( ctx.enclosing_stack.pop_back() );

    using encloser   = lexemes::encloser<Char>;
    using sublexemes = typename encloser::sublexemes;
    using subcode    = typename encloser::subcode;
    using splitter   = lexemes::splitter<Char>;
    using blob       = lexemes::blob<Char>;

    auto ret = encloser{ &me };
    if(me.lex_inner) ret.inner = sublexemes{};
    else             ret.inner = subcode{};

    /* Stuff to automate boilerplate. */

    // Returns a string_view of some span until the first '\n'.
    auto const until_newline = [](auto span) -> std::string_view
    {
        using namespace std::literals;

        if(span.size() == 0) return "\\0";
        if(starts_with(span, "\n"sv)) return "\\n";
        else if(starts_with(span, "\r"sv)) return "\\r";

        auto begin = span.data();
        auto len = 0_u64;
        while(span.size() && !starts_with_any(span, "\n"sv, "\r"sv) ) { ++len; span = span.subspan(1); };

        return {begin, len};
    };

    auto const push_encloser = [&](encloser&& e)
    {
        debug("+ pushing encloser <", e.encloser->name.data(), ">\n");
        ret.inner.template as<sublexemes>().push_back( KOL_MOV(e) );
    };
    auto const push_splitter = [&](auto s)
    {
        debug("+ pushing splitter <", s->name.data(), ">\n");
        ret.inner.template as<sublexemes>().push_back( splitter{ s } );
    };
    auto const push_blob_or_subcode = [&](auto data)
    {
        debug("+ pushing blob_or_subcode <", std::string_view{ data.begin(), data.end() }, ">\n");
        ret.inner
            .template on<sublexemes>([&](auto& l){ l.push_back(blob{ data }); })
            .template on<subcode>([&](auto& c){ c = data; });
    };

    /* Stuff for checking for matches. */

    auto const consider_matches = !me.is_discarded && me.lex_inner;

    typename lang<Char>::splitter const* splitter_match = nullptr;
    typename lang<Char>::encloser const* encloser_match = nullptr;
    auto const try_match_splitter =  [&]
    {
        for(auto& s : ctx.target_lang.splitters)
            if(s.is_begin(ctx.remaining)) { splitter_match = &s; return true; }
        return false;
    };
    auto const try_match_encloser =  [&]
    {
        for(auto& e : ctx.target_lang.enclosers)
            if(e.is_begin(ctx.remaining)) { encloser_match = &e; return true; }
        return false;
    };

    auto const sublexemes_size = [&]
    {
        auto size = -1;
        ret.inner.template on<sublexemes>([&](auto ls){ size = ls.size(); });
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
        if(acc_len) push_blob_or_subcode(std::span<Char>{acc, acc_len});
        reset_acc = true;

        push_splitter(splitter_match);
        advance = splitter_match->size;
    };
    auto do_encloser_match = [&]
    {
        if(acc_len) push_blob_or_subcode(std::span<Char>{acc, acc_len});
        reset_acc = true;

        ctx.enclosing_stack.push_back(encloser_match);
        end_prematurely = ctx.advance(encloser_match->begin_size) != encloser_match->begin_size;
        lex_enclosing(ctx)
            .template on< lexemes::encloser<Char> >([&](auto& e){ push_encloser(KOL_MOV(e)); })
            .template on< discarded >([&](auto){ debug("- <", encloser_match->name.data(), "> discarded\n"); }) // no-op.
            .template on< failed >([&](auto){ end_prematurely = true; });
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

        debug(sublexemes_size(), ": <", until_newline(ctx.remaining), ">\n");

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

        if(done && !me.is_discarded && acc_len) push_blob_or_subcode(std::span<Char>{acc, acc_len});
        else acc_len += advance;
    }

    if(!done || end_prematurely) return failed{};
    else if(me.is_discarded)     return discarded{};
    else                         return ret;
}
