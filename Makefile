bindir = /usr/local/bin
etcdir = /etc
wwwdir = /var/www/html
logdir = /var/log

#CFLAGS = --std=c99

#all: openvdm

#clean:
#	rm -f hithere hithere.o

install:install -d .$(logdir)OpenVDM $(logdir)

#	install -d .$(wwwdir)/OpenVDMv2 $(wwwdir)
#	install -d .$(bindir)/OpenVDMv2 $(bindir)
#	install -d .$(logdir)OpenVDM $(logdir)
#	install -m 0644 .$(etcdir)/apache2/sites-available/openvdm.conf.example $(etcdir)/apache2/sites-available
#	install -d .$(etcdir)/supervisor/conf.d/*.conf $(etcdir)/supervisor/conf.d

#	install -m 0644 hithere.1 $(DESTDIR)$(man1dir)
