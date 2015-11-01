[OpenVDMv2_Logo]: http://www.oceandatarat.org/wp-content/uploads/2014/11/openVDM_LogoV2_1_long.png "Open Vessel Data Managment v2" 

![OpenVDMv2_Logo]
#Open Vessel Data Management v2

##Installation Guide
At the time of this writing OpenVDMv2 was built and tested against the Xubuntu 14.04 LTS operating system. It may be possible to build against other linux-based operating systems however for the purposes of this guide the instructions will assume Xubuntu 14.04 LTS is used.

###Operating System
Goto <http://xubuntu.org/getxubuntu/>

Download Xubuntu for your hardware.  At the time of this writing we are using 14.04.3 (32-bit)

Perform the default Xubuntu install.  For these instructions the default account that is created is "Survey" and the computer name is "Warehouse".

A few minutes after the install completes and the computer restarts, Xubuntu will ask to install any updates that have arrived since the install image was created.  Perform these now and do not continue with these instructions until the update has completed.

Before OpenVDMv2 can be installed serveral other services and software packaged must be installed and configured.

###SSH Client/Server
SSH is used thoughout OpenVDM for providing secure communication between the Warehouse and other workstations aboard the vessel.  SSH is also used for OpenVDM's ship-to-shore communications.

To install SSH open a terminal window and type:
```
sudo apt-get install ssh sshpass
```

###Rsync
Rsync is used thoughout OpenVDM for providing efficient data transfers to/from the Warehouse.

To install rsync open a terminal window and type:
```
sudo apt-get install rsync
```

###Samba
One of the ways OpenVDM communicates with data collection system is through Windows Shares configured on the collection system workstation.  Windows shares are also configured on the data warehouse to allow scientists and crew to easily access data stored on the Warehouse from their Windows or Mac Laptops.  Windows shares on a non-windows machine are made possible thanks to the Samba project.  

To install Samba open a terminal window and type:
```
sudo apt-get install samba smbclient cifs-utils
```

Initialize the username creating during the OS installation for samba.  Change the username in the command below to the appropriate username for the current installation.  When prompted, set the password to the same password set of the user during the OS installation.
```
sudo smbpasswd -a survey
```

###ProFTPd
One of the ways users communicate with OpenVDMv2 is through an FTP server configured on the data warehouse.

To install ProFTPd open a terminal window and type:
```
sudo apt-get install proftpd
```


###MySQL Database Server
All of the commonly used variables, tranfer profiles, and user creditials for OpenVDM are stored in a SQL database.  This allows fast access to the stored information as well as a proven mechanism for multiple clients to change records without worry of write collisions.  OpenVDM uses the MySQL open-source database server.

To install MySQL open a terminal window and type:
```
sudo apt-get install mysql-server
```

###PHP5
The language used to write the OpenVDMv2 web-interface is PHP.

To install PHP open a terminal window and type:
```
sudo apt-get install php5 php5-cli php5-mysql
```

###Apache2 Web-server
The OpenVDM web-application is served by the Warehouse via the Apache2 Web-Server

Apache2 is installed by Xubuntu by default but an Apache2 module must be enabled.  To enable the additional module open a terminal window and type:
```
sudo a2enmod rewrite
```

After enabling the module the webserver must be restarted:
```
sudo service apache2 restart
```

###Gearman and Supervisor
Behind the OpenVDM web-application are several background processes that perform the various data transfers and other tasks.  Managing these background processes is a job broker and processes manager.

The job broker listens for requests to perform a specific task.  Once a request has arrived, the job broker farms the task out to the next available process that can perform that specific task.  OpenVDM uses Gearman as it's job broker.

Making sure the right type and number of worker processes are available to Gearman is the role of the process manager.  OpenVDM uses Supervisor as it's process manager.

#### Installing Gearman
To install Gearman open and terminal window and type the following commands:
```
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:gearman-developers/ppa
sudo apt-get update
sudo apt-get install gearman-job-server libgearman-dev php5-gearman python-gearman
sudo apt-get upgrade
```

Restart the Gearman Job Broker
```
sudo service gearman-job-server restart
```

OpenVDM requires that php5 be integrated with Gearman. To do that `extension=gearman.so` must be added to `/etc/php5/cli/php` and `/etc/php5/apache2/php`.

Modifying these files requires root privledges:
```
sudo nano /etc/php5/cli/php.ini
sudo nano /etc/php5/apache2/php.ini
```

Within each of these files is a section called `Dynamic Extensions`.  Most of these section is probably commented out.  Simple add `extension=gearman.so` to the end of the section.

Restart Apache
`sudo service apache2 restart`

#### Installing Supervisor
To install Supervisor open and terminal window and type the following command:
```
sudo apt-get install supervisor
```

Add the following lines to `/etc/supervisor/supervisor.conf`:

```
[inet_http_server]
port = 9001
```

Editing this file will require root privledges.
```
sudo nano /etc/supervisor/supervisor.conf
```

Restart Supervisor:
```
sudo service supervisor restart
```

Verify the istallation was successful by going to <http://127.0.0.1:9001>.

###Gearman-UI
Gearman-UI is not directly part of OpenVDM or the Gearman job broker however it is extremely useful when troubleshooting problems with Gearman.

####Installing composer

From a terminal window type:
```
sudo apt-get install curl
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
```

####Install bower
```
sudo apt-get install npm nodejs-legacy
sudo npm install -g bower
```

####Install Gearman-UI
Download the code from GitHub
```
sudo apt-get install git
git clone git://github.com/gaspaio/gearmanui.git ~/gearman-ui
```

Configure the site using the default configuration file
```
cd ~/gearman-ui
composer install --no-dev
bower install
cp config.yml.dist config.yml
```

Move the site to where Apache2 can access it.
```
cd
sudo mv gearman-ui /var/www/
sudo chown -R root:root /var/www/gearman-ui
```

Edit the default Apache2 VHost file.
```
sudo nano /etc/apache2/sites-available/000-default.conf
```

Copy text below into the Apache2 configuration file just above `</VirtualHost>`.
```
  Alias /gearman-ui /var/www/gearman-ui/web
  <Directory "/var/www/gearman-ui/web">
    <IfModule mod_rewrite.c>
      Options -MultiViews
      RewriteEngine On
      RewriteBase /gearman-ui/
      RewriteCond %{REQUEST_FILENAME} !-f
      RewriteRule ^ index.php [QSA,L]
    </IfModule>
  </Directory>
```

Reload Apache2
```
sudo service apache2 reload
```

Verify the installation was successful by going to: <http://127.0.0.1/gearman-ui>

###MapProxy
In order to add GIS capability to OpenVDMv2 without eccessive requests to the internet for baselayer tiles a map tile proxy needs to be installed.

Install the dependencies
```
sudo apt-get install python-imaging python-yaml libproj0 libgeos-dev python-lxml libgdal-dev python-shapely
```

Install MapProxy
```
sudo pip install MapProxy
```

Build the initial configuration
```
cd
mapproxy-util create -t base-config mapproxy
```

Copy the following into `~/mapproxy/mapproxy.yaml`
```
# -------------------------------
# MapProxy configuration.
# -------------------------------

# Start the following services:
services:
  demo:
  tms:
    use_grid_names: true
    # origin for /tiles service
    origin: 'nw'
  kml:
    #use_grid_names: true
  wmts:
  wms:
    srs: ['EPSG:900913']
    image_formats: ['image/png']
    md:
      title: MapProxy WMS Proxy
      abstract: This is a minimal MapProxy installation.

#Make the following layers available
layers:
  - name: WorldOceanBase
    title: ESRI World Ocean Base
    sources: [esri_worldOceanBase_cache]

  - name: WorldOceanReference
    title: ESRI World Ocean Reference
    sources: [esri_worldOceanReference_cache]

caches:
  esri_worldOceanBase_cache:
    grids: [esri_online]
    sources: [esri_worldOceanBase]

  esri_worldOceanReference_cache:
    grids: [esri_online]
    sources: [esri_worldOceanReference]

sources:
  esri_worldOceanBase:
    type: tile
    url: http://server.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/%(z)s/%(y)s/%(x)s.png
    grid: esri_online

  esri_worldOceanReference:
    type: tile
    transparent: true
    url: http://server.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/%(z)s/%(y)s/%(x)s.png
    grid: esri_online

grids:
  webmercator:
    base: GLOBAL_WEBMERCATOR

  esri_online:
     tile_size: [256, 256]
     srs: EPSG:900913
     origin: 'nw'
     #num_levels: 25

globals:
```

Move the installation to it's final location and set the user/group ownership
```
sudo cp ~/mapproxy /var/www/
sudo mkdir /var/www/mapproxy/cache_data
sudo chmod 777 /var/www/mapproxy/cache_data
sudo chown -R root:root /var/www/mapproxy
```

Prepare Apache2 to host the MapProxy installation
```
sudo apt-get install libapache2-mod-wsgi
```

Prepare the MapProxy installation for integration with the Apache2 web-server
```
cd /var/www/mapproxy
sudo mapproxy-util create -t wsgi-app -f mapproxy.yaml config.py
```

Edit the apache conf

```
sudo pico /etc/apache2/sites-available/000-default
```

Add the following just above `</VirutalHost>` at the end of the file

```
WSGIScriptAlias /mapproxy /var/www/mapproxy/config.py

<Directory /var/www/mapproxy/>
  Order deny,allow
  Allow from all
</Directory>
```

Restart Apache2

```
sudo service apache2 restart
```

Verify the installation works by going to `http://<servername or IP>/mapproxy/demo/`

###OpenVDMv2

####Create the Required Directories
In order for OpenVDMv2 to properly store data serveral directories must be created on the Warehouse

 - **FTPRoot** - This will become the document root for the ProFTP server. 
 - **CruiseData** - This is the location where the Cruise Data directories will be located.  This directory needs to live within the **FTPRoot**
 - **PublicData** - This is the location where the Public Data share will be located.  This directory needs to live within the **FTPRoot**
 - **VisitorInformation** - This is the location where ship-specific information will be located.  This directory needs to live within the **FTPRoot**

The Location of the **FTPRoot** needs to be large enough to hold multiple cruises worth of data.  In typical installation of OpenVDMv2, the location of the **FTPRoot** is on dedicated hardware (internal RAID array).  In these cases the volume is mounted at boot by the OS to a specific location (i.e. `/mnt/vault`).  Instructions on mounting volumes at boot is beyond the scope of these installation procedures however.

For the purposes of these installation instructions the parent folder for **FTPRoot** will be a large RAID array located at: `/mnt/vault` and the user that will retain ownership of these folders will be "survey"

```
sudo mkdir -p /mnt/vault/FTPRoot/CruiseData
sudo mkdir -p /mnt/vault/FTPRoot/PublicData
sudo mkdir -p /mnt/vault/FTPRoot/VistorInformation
sudo chown -R survey:survey /mnt/vault/FTPRoot/*
```

####Download the OpenVDM Files from Github

From a terminal window type:
```
git clone git://github.com/webbpinner/OpenVDMv2.git ~/OpenVDMv2
```

####Create OpenVDMv2 Database
To create a new database first connect to MySQL by typing:
```
mysql -h localhost -u root -p
```

Once connected to MySQL, create the database by typing:
```
CREATE DATABASE OpenVDMv2;
```

Now create a new MySQL user specifically for interacting with only the OpenVDM database.  In the example provided below the name of the user is `openvdmDBUser` and the password for that new user is `oxhzbeY8WzgBL3`.
```
GRANT ALL PRIVILEGES ON OpenVDMv2.* To openvdmDBUser@localhost IDENTIFIED BY 'oxhzbeY8WzgBL3';
```

It is not important what the name and passwork are for this new user however it is important to remember the designated username/password as it will be reference later in the installation.

To build the database schema and perform the initial import type:
```
USE OpenVDMv2;
source ~/OpenVDMv2/OpenVDMv2_db.sql;
```

Exit the MySQL console:
```
exit
```

####Install OpenVDMv2 Web-Application

Copy the web-application code to a directory that can be accessed by Apache

```
sudo cp -r ~/OpenVDMv2/var/www/OpenVDMv2 /var/www/
sudo chown -R root:root /var/www/OpenVDMv2
```

Create the two required configuration files from the example files provided.
```
cd /var/www/OpenVDMv2
sudo cp ./.htaccess.dist ./.htaccess
sudo cp ./app/Core/Config.php.dist ./app/Core/Config.php
```

Modify the two configuration files.

Edit the `.htaccess` file:
```
sudo nano /var/www/OpenVDMv2/.htaccess
```

 - Set the `RewriteBase` to part of the URL after the hostname that will become the landing page for OpenVDMv2.  By default this is set to `OpenVDMv2` meaning that once active users will go to http://<hostname or IP>/OpenVDMv2/.

Edit the `./app/Core/Config.php` file:
```
sudo nano /var/www/OpenVDMv2/app/Core/Config.php
```

 - Set the file URL of the OpenVDMv2 installation.  Look for the following lines and change the IP address in the URL to the actual IP address or hostname of the warehouse:
```
//site address
define('DIR', 'http://127.0.0.1/OpenVDMv2/');
```

**A word of caution.** The framework used by OpenVDMv2 does not allow more than one URL to access the web-application.  This means that you can NOT access the web-application using the machine hostname AND IP.  You must pick one.  Also with dual-homed machines you CAN NOT access the web-application by entering the IP address of the interface not used in this configuration file.  Typically this is not a problem since dual-homed installation are dual-homed because the Warehouse is spanning a public and private subnet.  While users on the the public subnet can't access machines on the private network, users on the private network can access machines on the public network.  In that scenario the URL should be set to the Warehouse's interface on the public network, thus allowing users on both subnets access.

 - Set the access creditials for the MySQL database.  Look for the following lines and modify them to fit the actual database name (`DB_NAME`), database username (`DB_USER`), and database user password (`DB_PASS`).
```
//database details ONLY NEEDED IF USING A DATABASE
define('DB_TYPE', 'mysql');
define('DB_HOST', 'localhost');
define('DB_NAME', 'OpenVDMv2');
define('DB_USER', 'openvdmDBUser');
define('DB_PASS', 'oxhzbeY8WzgBL3');
define('PREFIX', 'OVDM_');
```

Edit the default Apache2 VHost file.
```
sudo nano /etc/apache2/sites-available/000-default.conf
```

Copy text below into the Apache2 configuration file just above `</VirtualHost>`.  You will need to alter the directory locations to match the locations selected for the **CruiseData**, **PublicData** and **VisitorInformation** directories:
```
  Alias /OpenVDMv2 /var/www/OpenVDMv2
  <Directory "/var/www/OpenVDMv2">
    AllowOverride all
  </Directory>
  
  Alias /CruiseData/ /mnt/vault/FTPRoot/CruiseData/
  <Directory "/mnt/vault/FTPRoot/CruiseData">
    AllowOverride None
    Options +Indexes +FollowSymLinks +MultiViews
    Order allow,deny
    Allow from all
    Require all granted
  </Directory>

  Alias /PublicData/ /mnt/vault/FTPRoot/PublicData/
  <Directory "/mnt/vault/FTPRoot/PublicData">
    AllowOverride None
    Options +Indexes +FollowSymLinks +MultiViews
    Order allow,deny
    Allow from all
    Require all granted
  </Directory>

  Alias /VisitorInformation/ /mnt/vault/FTPRoot/VisitorInformation/
  <Directory "/mnt/vault/FTPRoot/VisitorInformation">
    AllowOverride None
    Options +Indexes +FollowSymLinks +MultiViews
    Order allow,deny
    Allow from all
    Require all granted
  </Directory>
```

Reload Apache2
```
sudo service apache2 reload
```

Additionally a log directory must be created for the OpenVDMv2 web-application
```
sudo mkdir /var/log/OpenVDM
```

####Install OpenVDMv2 Processes
Copy the OpenVDMv2 processes to the `/usr/local/bin` folder
```
sudo cp -r ~/OpenVDMv2/usr/local/bin/* /usr/local/bin/
```

####Install the Supervisor configuration files
```
sudo cp -r ~/OpenVDMv2/etc/supervisor/conf.d/* /etc/supervisor/conf.d/
```

####Modify the configuation file for the OpenVDMv2 scheduler
```
sudo nano /etc/supervisor/conf.d/OVDM
```
Look for the following line:
```
command=/usr/bin/python /usr/local/bin/OVDM_scheduler.py --interval 5 http://127.0.0.1/OpenVDMv2/
```

Change the URL to match the URL specified in the Config.php file during the OpenVDMv2 web-application installation.

Restart Supervisor
```
sudo service supervisor
```

####Setup the Samba shares


```
obey pam restrictions = no
```

Add to end of the `smb.conf` file.  Set the user in `write list` to the username created during the OS the installation:
```
[CruiseData]
  comment=Cruise Data, read-only access to guest
  path=/mnt/vault/FTPRoot/CruiseData
  browsable = yes
  public = yes
  guest ok = yes
  writable = yes
  write list = survey
  create mask = 0644
  directory mask = 0755
  veto files = /._*/.DS_Store/
  delete veto files = yes

[VisitorInformation]
  comment=Visitor Information, read-only access to guest
  path=/mnt/vault/FTPRoot/VisitorInformation
  browsable = yes
  public = yes
  guest ok = yes
  writable = yes
  write list = survey
  create mask = 0644
  directory mask = 0755
  veto files = /._*/.DS_Store/
  delete veto files = yes

[PublicData]
  comment=Public Data, read/write access to all
  path=/mnt/vault/FTPRoot/PublicData
  browseable = yes
  public = yes
  guest ok = yes
  writable = yes
  create mask = 0000
  directory mask = 0000
  veto files = /._*/.DS_Store/
  delete veto files = yes
  force create mode = 666
  force directory mode = 777
```

Restart the Samba service
```
sudo service samba restart
```

At this point the warehouse should have a working installation of OpenVDMv2 however the vessel operator will still need to configure collection system transfers, cruise data transfers and the shoreside data warehouse.
