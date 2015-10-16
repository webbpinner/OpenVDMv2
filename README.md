[OpenVDMv2_Logo]: http://www.oceandatarat.org/wp-content/uploads/2014/11/openVDM_LogoV2_1_long.png "Open Vessel Data Managment v2" 

![OpenVDMv2_Logo]
#Open Vessel Data Management v2

##Installation
Goto http://xubuntu.org/getxubuntu/

Download Xubuntu for your hardware.  At the time of this writing we are using 14.04.3 (32-bit)

Perform the default Xubuntu install.  For these instructions the default account that is created is "Survey" and the computer name is "Warehouse".

A few minutes after the install completes and the computer restarts, Xubuntu will ask to install any updates that have arrived since the install image was created.  Perform these now and do not continue with these instructions until the update has completed.

###Install the SSH client/server
SSH is used thoughout OpenVDM for providing secure communication between the Warehouse and other workstations abouard the vessel.  SSH is also used for OpenVDM's ship-to-shore communications.

To install SSH open a terminal window and type:
`apt-get install ssh sshpass`

###MySQL Database
`apt-get install mysql-server`

###PHP5
`apt-get install php5 php5-cli php5-mysql`

maybe --> php-pear php5-dev

###Apache2 Web-server
`apt-get install apache2 libapache2-mod-php5 libapache2-mod-mysql`

###Samba
`apt-get install samba smbclient`

###Supervisor
`apt-get install supervisor`

Add `[inet_http_server]` to `/etc/supervisor/supervisor.conf`

`nano /etc/supervisor/supervisor.conf`

###Miscellaneous Packages
`apt-get install rsync curl git gdal-bin python-gdal`
maybe --> npm nodejs-legacy

###Gearman
`apt-get install software-properties-common`
`add-apt-repository ppa:gearman-developers/ppa`
`apt-get update`
`apt-get install gearm-job-server libgearman-dev php5-gearman python-gearman`
`apt-get upgrade`

Add `extension=gearman.so` to `/etc/php5/cli/php`

`nano /etc/php5/cli/php.ini`

Add `extension=gearman.so` to `/etc/php5/apache2/php`

`nano /etc/php5/apache2/php.ini`

Restart Apache
`service apache2 restart`

###MapProxy
`apt-get install mapproxy`


gearman

sudo pecl install gearman

###Install Composer
curl-sS https://getcomposer.org/installer | php
mv Composer.phar /usr/local/bin

gdal-bin python-gdal
npm nodejs-legacy

