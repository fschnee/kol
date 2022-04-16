// I don't like std::variant, too verbose and heavy.
#pragma once

#include "kol/utils/utility.hpp"

namespace kol { template <class...> struct variant; }

// Can only handle variants with more than 1 type.
// Advertises copyability to work with incomplete types.
template <class... Ts>
struct kol::variant
{
    constexpr auto is_valid() const { return index != sizeof...(Ts); }
    template <class T>
    constexpr auto holds()    const { return tl::index_of<T, variant>::value == index; }
    template <u64 I>
    constexpr auto holds() const
    requires tl::indexed<I, variant>::value
    { return holds< typename tl::indexed<I, variant>::type >(); }

    template <class T, class Functor>
    constexpr auto on(Functor&& f) const -> variant const&
    {
        if(holds<T>()) f( as<T>() );
        return *this;
    }

    template <class T, class Functor>
    constexpr auto on(Functor&& f) -> variant&
    {
        if(holds<T>()) f( as<T>() );
        return *this;
    }

    template <class T> constexpr auto as()       -> T&       { return *reinterpret_cast<T*>(&data); }
    template <class T> constexpr auto as() const -> T const& { return *reinterpret_cast<T const*>(&data); }

    template <u64 I> constexpr auto as() -> typename tl::indexed<I, variant>::type&
    requires tl::indexed<I, variant>::value
    { return *reinterpret_cast< typename tl::indexed<I, variant>::type* >(&data); }

    template <u64 I> constexpr auto as() const -> typename tl::indexed<I, variant>::type const&
    requires tl::indexed<I, variant>::value
    { return *reinterpret_cast< typename tl::indexed<I, variant>::type const* >(&data); }

    constexpr variant() = default;

    template <typename T>
    constexpr variant(T&& t)
    requires tl::contains<T, variant>::value
    { *this = emplaced<T>(KOL_FWD(t)); }

    template <class T>
    static constexpr auto emplaced(auto&&... args) -> variant
    requires tl::contains<T, variant>::value
    {
        auto ret = variant{};

        new (&ret.data) T(KOL_FWD(args)...);
        ret.index   = tl::index_of<T, variant>::value;
        ret.copy    = [](auto src, auto tgt) { new (&tgt.data) T(src.template as<T>()); };
        ret.destroy = [](auto v)             { v.template as<T>().~T(); };

        return ret;
    }

    constexpr variant(const variant& other)     { *this = other; }
    constexpr variant(variant&& other) noexcept { *this = KOL_MOV(other); }

    constexpr auto operator=(const variant& other) -> variant&
    {
        destroy(*this);

        index   = other.index;
        copy    = other.copy;
        destroy = other.destroy;
        if(is_valid()) copy(other, *this);

        return *this;
    }

    constexpr auto operator=(variant&& other) noexcept -> variant&
    {
        swap(index, other.index);
        swap(data, other.data);
        swap(copy, other.copy);
        swap(destroy, other.destroy);

        return *this;
    }

    ~variant() { destroy(*this); }

private:
    unsigned long long index = sizeof...(Ts);

    using data_t = std::aligned_storage_t< max(sizeof(Ts)...), max(alignof(Ts)...) >;
    data_t data;

    using copy_t    = void(*)(variant const&, variant&);
    using destroy_t = void(*)(variant&);

    copy_t copy       = [](auto, auto){};
    destroy_t destroy = [](auto){};
};
