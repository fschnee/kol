#pragma once

#include "kol/utils/aliases.hpp"

namespace kol
{
    template <class T> struct remove_ref      { using type = T; };
    template <class T> struct remove_ref<T&>  { using type = T; };
    template <class T> struct remove_ref<T&&> { using type = T; };

    template <bool B, class T = void> struct enable_if {};
    template <class T> struct enable_if<true, T> { using type = T; };
    template <bool B, class T = void> using enable_if_t = typename enable_if<B,T>::type;

    #define KOL_FWD(x) static_cast<decltype(x)&&>(x)
    #define KOL_MOV(x) static_cast<typename kol::remove_ref<decltype(x)>::type&& >(x)

    constexpr auto swap(auto& a, auto& b)
    {
        auto c = KOL_MOV(a);
        a = KOL_MOV(b);
        b = KOL_MOV(c);
    }

    constexpr auto max(auto arg1, auto arg2, auto... args)
    {
        if constexpr (sizeof...(args) > 0) return arg1 > arg2 ? max(arg1, args...) : max(arg2, args...);
        else                               return arg1 > arg2 ? arg1               : arg2;
    }

    template <auto v> struct val { static constexpr auto value = v; };

    // Stuff for dealing with type lists.
    namespace tl
    {
        template <class, class> struct index_of;
        // Base cases.
        template <class T, template <class...> class L>              struct index_of<T, L<>>         : val<0_u64> {};
        template <class T, template <class...> class L, class... Ts> struct index_of<T, L<T, Ts...>> : val<0_u64> {};
        // Recursive case.
        template <class T, class Other, template <class...> class L, class... Ts>
        struct index_of<T, L<Other, Ts...>> : val< 1 + index_of<T, L<Ts...>>::value > {};

        template <class, class> struct contains;
        template <class T, template <class...> class L, class... Ts>
        struct contains<T, L<Ts...>> : val< index_of<T, L<Ts...>>::value != sizeof...(Ts) > {};
    }

    constexpr auto starts_with(auto span, auto span2) -> bool
    {
        if(span.size() < span2.size()) return false;

        for(auto i = 0_u64; i < span2.size(); ++i)
            if(span[i] != span2[i]) return false;

        return true;
    }

    constexpr auto starts_with_any(auto span, auto... spans) -> bool
    { return (starts_with(span, spans) || ...); }
}
