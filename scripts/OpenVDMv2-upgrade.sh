#!/bin/bash

sudo rsync -avi ../var/www/OpenVDMv2 /var/www/
sudo chown -R www-data:www-data /var/www/OpenVDMv2
sudo chmod -R 644 /var/www/OpenVDMv2
sudo chmod -R +X /var/www/OpenVDMv2

sudo rsync -avi ../usr/local/etc/openvdm/* /usr/local/etc/openvdm/

sudo rsync -avi ../usr/local/bin/OVDM_* /usr/local/bin/
sudo chown -R root:root /usr/local/bin/OVDM_*
sudo chmod -R 644 /usr/local/bin/OVDM_*
sudo chmod -R +X /usr/local/bin/OVDM_*

sudo rsync -avi ../usr/local/bin/openvdm.py /usr/local/bin/
sudo chown -R root:root /usr/local/bin/openvdm.py
sudo chmod -R 755 /usr/local/bin/openvdm.py

sudo rsync -avi ../etc/supervisor/conf.d/* /etc/supervisor/conf.d/

#sudo systemctl stop supervisor.service
#sudo systemctl restart gearman-job-server.service
#sudo systemctl start supervisor.service

