#pragma once

#include "kol/utils/dont_forget.hpp"

#include <string_view>
#include <cstdio>
#include <string>

namespace kol::app::inline cmdline
{
    struct cmdline_flags
    {
        bool interp = false;
        std::string code = "";
    };

    inline auto parse_args(char const** begin, char const** end) -> cmdline_flags
    {
        auto cmd = cmdline_flags{};

        auto next_is_code = false;
        for(auto it = begin; it != end; ++it)
        {
            auto arg = std::string_view{*it};

            if(next_is_code)
            {
                cmd.code = arg;
                next_is_code = false;
            }
            else if(arg == "--interp" || arg == "-i") cmd.interp = true;
            else if(arg == "--code"   || arg == "-c") next_is_code = true;
            else {
                auto fp = std::fopen(arg.data(), "r");
                if(fp == nullptr) { std::printf("Error opening file %s\n", arg.data()); continue; }
                KOL_DONT_FORGET( std::fclose(fp) );

                std::fseek(fp, 0, SEEK_END);
                auto codesize = std::ftell(fp);
                std::fseek(fp, 0, SEEK_SET);

                cmd.code.resize(codesize);
                std::fread(cmd.code.data(), sizeof(uint8_t), codesize, fp);
            }
        }

        return cmd;
    }
}
