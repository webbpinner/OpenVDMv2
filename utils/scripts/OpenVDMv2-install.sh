#!/bin/bash

sudo rsync -avi ../var/www/OpenVDMv2 /var/www/
sudo cp /var/www/OpenVDMv2/.htaccess.dist /var/www/OpenVDMv2/.htaccess
sudo cp /var/www/OpenVDMv2/app/Core/Config.php.dist /var/www/OpenVDMv2/app/Core/Config.php
sudo touch /var/www/OpenVDMv2/errorlog.html
sudo chmod 777 /var/www/OpenVDMv2/errorlog.html
sudo chown -R root:root /var/www/OpenVDMv2

sudo mkdir -p /usr/local/etc/openvdm
sudo rsync -avi ../usr/local/etc/openvdm/* /usr/local/etc/openvdm/
sudo cp /usr/local/etc/openvdm/datadashboard.yaml.dist /usr/local/etc/openvdm/datadashboard.yaml
sudo cp /usr/local/etc/openvdm/openvdm.yaml.dist /usr/local/etc/openvdm/openvdm.yaml

sudo mkdir -p /var/log/OpenVDM

sudo rsync -aiv ../usr/local/bin/* /usr/local/bin/

sudo rsync -aiv ../etc/supervisor/conf.d/* /etc/supervisor/conf.d/
sudo mv /etc/supervisor/conf.d/OVDM_runCollectionSystemTransfer.conf.dist /etc/supervisor/conf.d/OVDM_runCollectionSystemTransfer.conf
sudo mv /etc/supervisor/conf.d/OVDM_postCollectionSystemTransfer.conf.dist /etc/supervisor/conf.d/OVDM_postCollectionSystemTransfer.conf
