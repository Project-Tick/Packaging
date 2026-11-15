# What the MultiMC wrapper package installs, and where: the one list every package format uses
# (deb, rpm and Arch call `make install DESTDIR=...`; see build.py and README.md).
#
# The wrapper itself is run.sh: its first start downloads the current Stable build of MultiMC
# into the user's data folder. Desktop file, icon and metainfo are named org.multimc.MultiMC,
# the Launcher's Wayland app id, and the desktop file's StartupWMClass is its X11 window class.

DESTDIR ?=
ID = org.multimc.MultiMC

.PHONY: install
install:
	install -Dm755 files/run.sh $(DESTDIR)/opt/multimc/run.sh
	install -Dm644 files/icon.svg $(DESTDIR)/opt/multimc/icon.svg
	install -Dm644 files/$(ID).desktop $(DESTDIR)/usr/share/applications/$(ID).desktop
	install -Dm644 files/icon.svg $(DESTDIR)/usr/share/icons/hicolor/scalable/apps/$(ID).svg
	install -Dm644 files/$(ID).metainfo.xml $(DESTDIR)/usr/share/metainfo/$(ID).metainfo.xml
	install -Dm644 files/multimc.1 $(DESTDIR)/usr/share/man/man1/multimc.1
	install -d $(DESTDIR)/usr/bin
	ln -sf /opt/multimc/run.sh $(DESTDIR)/usr/bin/multimc
