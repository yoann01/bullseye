prefix=/usr
LIBDIR=$(DESTDIR)$(prefix)/lib
BIN=$(DESTDIR)$(prefix)/bin
DATADIR=$(DESTDIR)$(prefix)/share
LOCALEDIR=$(DATADIR)/locale
MANDIR=$(DATADIR)/man

all:
clean:
	rm -f locale/*/LC_MESSAGES/bullseye.mo
	rm -f bullseye.1.gz


install:
	install -d $(LOCALEDIR) $(BIN) $(DATADIR)/bullseye


	install -m644 trunk/Bullseye.desktop $(DATADIR)/applications
	install -m644 trunk/icons/bullseye.png $(DATADIR)/pixmaps
	install -m755 trunk/bullseye $(BIN)

	for sourcedir in `find trunk/ -type d | grep -v '.svn' | grep -v '.pyc' | sed 's:trunk/::g'` ; do \
		install -d $(DATADIR)/bullseye/$$sourcedir; \
		for sourcefile in `find trunk/$$sourcedir -maxdepth 1 -type f | grep -v '.svn' | grep -v '.pyc'` ; do \
			install -m644 $$sourcefile $(DATADIR)/bullseye/$$sourcedir; \
		done \
	done

	install -m755 trunk/bullseye_qt.py $(DATADIR)/bullseye
	install -m644 trunk/core.py $(DATADIR)/bullseye
	install -m644 trunk/bullseye.py $(DATADIR)/bullseye

uninstall:
	rm -f $(DATADIR)/applications/Bullseye.desktop
	rm -f $(DATADIR)/pixmaps/bullseye.png
	rm -f $(BIN)/bullseye
	rm -f $(MANDIR)/man1/bullseye.1.gz
	rm -rf $(LIBDIR)/bullseye
	rm -rf $(DATADIR)/bullseye

	for gettextfile in `find $(LOCALEDIR) -name 'bullseye.mo'` ; do \
		rm -f $$gettextfile; \
	done
