#include "kol/app/cmdline.hpp"
#include "kol/lex.hpp"
///#include "kol/lex_print.hpp"

int main(int argc, const char* argv[])
{
    auto const args = kol::app::parse_args(argv+1, argv+argc);

    auto const code_span = std::span< decltype(args.code)::value_type const >(args.code.data(), args.code.size()-2);
    auto lexed = kol::lex(code_span);

    //kol::lexing::print(lexemes);
}
