#!/bin/bash
# In a Fedora container, by build.py: builds the rpm from /work/MultiMC5.spec and the source
# tarball, checks its desktop file, and puts the package into /work.
set -euo pipefail
version=$(cat /work/VERSION)
dnf -q -y install rpm-build make desktop-file-utils > /tmp/dnf.log 2>&1 || { cat /tmp/dnf.log; exit 1; }
mkdir -p ~/rpmbuild/SOURCES
cp "/work/multimc-wrapper-${version}.tar.gz" ~/rpmbuild/SOURCES/
rpmbuild --quiet -bb /work/MultiMC5.spec
rpm=$(find ~/rpmbuild/RPMS -name '*.rpm')
rpm -qlp "$rpm"
mkdir -p /tmp/check
(cd /tmp/check && rpm2cpio "$rpm" | cpio -idm --quiet)
desktop-file-validate /tmp/check/usr/share/applications/org.multimc.MultiMC.desktop
cp "$rpm" /work/
