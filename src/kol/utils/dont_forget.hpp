#pragma once

#include "kol/utils/utility.hpp"

namespace kol
{
    template <typename Func>
    struct dont_forget
    {
        constexpr dont_forget(Func&& oe) : on_exit{ KOL_FWD(oe) } {}

        dont_forget() = delete;
        dont_forget(dont_forget&&) = delete;
        dont_forget(const dont_forget&) = delete;
        auto operator=(dont_forget&&) -> dont_forget& = delete;
        auto operator=(const dont_forget&) -> dont_forget& = delete;

        ~dont_forget() { on_exit(); }

    private:
        Func on_exit;
    };
}

#define _KOL_DONT_FORGET_CONCAT_IMPL(x, y) x##y
#define _KOL_DONT_FORGET_CONCAT(x, y) _KOL_DONT_FORGET_CONCAT_IMPL(x, y)

#define KOL_DONT_FORGET( body ) \
    auto _KOL_DONT_FORGET_CONCAT(kol_reminder_on_line_, __LINE__) = kol::dont_forget{ [&]{ body; }}
