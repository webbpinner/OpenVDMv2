#!/bin/bash

# Config files
sudo rsync -avi /usr/local/etc/openvdm/openvdm.yaml.dist ../usr/local/etc/openvdm/
sudo rsync -avi /usr/local/etc/openvdm/datadashboard.yaml.dist ../usr/local/etc/openvdm/

# Web-related files
sudo rsync -avi --exclude="errorlog.html" --exclude=".htaccess" --exclude="Config.php" /var/www/OpenVDMv2 ../var/www/

# Scripts
sudo rsync -avi --exclude="OVDM_dashboardDataScripts" /usr/local/bin/OVDM_* ../usr/local/bin/
sudo rsync -avi /usr/local/bin/OVDM_dashboardDataScripts/*.dist ../usr/local/bin/OVDM_dashboardDataScripts

