#!/usr/bin/env sh

if [ ! -d "builddir" ]
then
    ./configure.sh
fi

meson compile -C builddir && ./builddir/kol "$@"
