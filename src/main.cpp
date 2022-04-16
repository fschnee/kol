#include "kol/app/cmdline.hpp"
#include "kol/lex.hpp"
#include "kol/lex_print.hpp"

int main(int argc, const char* argv[])
{
    auto const args = kol::app::parse_args(argv+1, argv+argc);

    using char_t = decltype(args.code)::value_type const;

    auto const code_span = std::span<char_t>(args.code.data(), args.code.size());

    auto kollang = kol::default_lang<char_t>();
    auto lexed = kol::lex(code_span, kollang);
    if(!lexed.holds<0>()) return 1; // TODO: handle failure
    auto& encloser = lexed.as<0>();
    kol::lexing::print(encloser);
}
