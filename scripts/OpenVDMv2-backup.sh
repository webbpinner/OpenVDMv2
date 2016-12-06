#!/bin/bash

mkdir -p ../backup/usr/local/etc/openvdm
cp /usr/local/etc/openvdm/datadashboard.yaml ../backup/usr/local/etc/openvdm/
cp /usr/local/etc/openvdm/openvdm.yaml ../backup/usr/local/etc/openvdm/

mkdir -p ../backup/var/www/OpenVDMv2/app/Core
cp /var/www/OpenVDMv2/.htaccess ../backup/var/www/OpenVDMv2/
cp /var/www/OpenVDMv2/app/Core/Config.php ../backup/var/www/OpenVDMv2/app/Core/

