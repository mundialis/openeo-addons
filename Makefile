MODULE_TOPDIR = ../..

SUBDIRS = \
	r.scaleminmax \
	t.rast.resample

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
