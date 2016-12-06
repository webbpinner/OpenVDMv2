#!/bin/bash

rsync -avi ../var/www/OpenVDMv2 /var/www/
cp /var/www/OpenVDMv2/.htaccess.dist /var/www/OpenVDMv2/.htaccess
cp /var/www/OpenVDMv2/app/Core/Config.php.dist /var/www/OpenVDMv2/app/Core/Config.php

mkdir -p /usr/local/etc/openvdm
rsync -avi ../usr/local/etc/openvdm/* /usr/local/etc/openvdm/
cp /usr/local/etc/openvdm/datadashboard.yaml.dist /usr/local/etc/openvdm/datadashboard.yaml
cp /usr/local/etc/openvdm/openvdm.yaml.dist /usr/local/etc/openvdm/openvdm.yaml

mkdir -p /var/log/OpenVDM

rsync -aiv ../usr/local/bin/* ./usr/local/bin/

rsync -aiv ../etc/supervisor/conf.d/* /etc/supervisor/conf.d/

