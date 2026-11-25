#!/bin/bash
# In an Arch container, by build.py: from /work/aur/PKGBUILD and the source tarball, writes the
# AUR's .SRCINFO next to the PKGBUILD, builds the package as a check, and runs namcap on both.
# makepkg refuses to run as root: it runs as a user of its own.
set -euo pipefail
version=$(cat /work/VERSION)
pacman -Syu --noconfirm --needed --quiet base-devel namcap > /tmp/pacman.log 2>&1 || { cat /tmp/pacman.log; exit 1; }
useradd -m builder
mkdir /build
cp /work/aur/PKGBUILD "/work/meshmc-wrapper-${version}.tar.gz" /build/
chown -R builder /build
cd /build
su builder -c "makepkg --printsrcinfo" > /work/aur/.SRCINFO
su builder -c "makepkg --nodeps --noconfirm" > /dev/null
pkg=$(ls /build/*.pkg.tar.*)
tar -tf "$pkg" | grep -v '^\.' | sort
namcap PKGBUILD "$pkg" || true
cp "$pkg" /work/
