# What the MeshMC wrapper package installs, and where: the one list every package format uses
# (deb, rpm and Arch call `make install DESTDIR=...`; see build.py and README.md).
#
# The wrapper itself is run.sh: its first start downloads the current Stable build of MeshMC
# into the user's data folder. Desktop file, icon and metainfo are named org.projecttick.MeshMC,
# the Launcher's Wayland app id, and the desktop file's StartupWMClass is its X11 window class.

DESTDIR ?=
PREFIX ?= /usr
ID = org.projecttick.MeshMC

.PHONY: install
install:
	install -Dm755 files/run.sh $(DESTDIR)$(PREFIX)/bin/meshmc
	install -Dm644 files/icon.svg $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/$(ID).svg
	install -Dm644 files/icon.png $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/$(ID).png
	install -Dm644 files/$(ID).desktop $(DESTDIR)$(PREFIX)/share/applications/$(ID).desktop
	install -Dm644 files/$(ID).metainfo.xml $(DESTDIR)$(PREFIX)/share/metainfo/$(ID).metainfo.xml
	install -Dm644 files/meshmc.1 $(DESTDIR)$(PREFIX)/share/man/man1/meshmc.1
