#!/bin/bash

rsync -avi ../var/www/OpenVDMv2 /var/www/

rsync -avi ../usr/local/etc/openvdm/* /usr/local/etc/openvdm/

rsync -avi ../usr/local/bin/OVDM_* /usr/local/bin/
rsync -avi ../usr/local/bin/openvdm.py /usr/local/bin/

rsync -avi ../etc/supervisor/conf.d/* /etc/supervisor/conf.d/

systemctl stop supervisor.service
systemctl restart gearman-job-server.service
systemctl start supervisor.service

