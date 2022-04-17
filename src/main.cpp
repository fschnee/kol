#include "kol/app/cmdline.hpp"
#include "kol/lang.hpp"

int main(int argc, const char* argv[])
{
    auto const args = kol::app::parse_args(argv+1, argv+argc);

    auto kol = kol::bootstrap_lang();
    kol.load_code(args.code, true);
}
