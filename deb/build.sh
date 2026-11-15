#!/bin/bash
# In a Debian container, by build.py: /work/deb-root is the installed tree with its DEBIAN/
# folder; makes /work/multimc_<version>-1.deb and lists what it holds.
set -euo pipefail
version=$(cat /work/VERSION)
deb=/work/multimc_${version}-1.deb
dpkg-deb --root-owner-group -Zxz --build /work/deb-root "$deb"
dpkg-deb --info "$deb"
dpkg-deb --contents "$deb"
