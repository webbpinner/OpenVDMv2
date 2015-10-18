[OpenVDMv2_Logo]: http://www.oceandatarat.org/wp-content/uploads/2014/11/openVDM_LogoV2_1_long.png "Open Vessel Data Managment v2" 

![OpenVDMv2_Logo]
#Open Vessel Data Management v2

OpenVDMv2 is a ship-wide data management solution.  It is comprised of suite of programs and an accompanying web-application that provides vessel operators with a unified interface for organizing files created by multiple data acquisition systems into a single cruises data package while a cruise is underway.  Once the files are in the cruise data package they are immediately accessible by scientists.  In addition, vessel operators can configure OpenVDM to regularly copy the cruise data package to backup storage devices, external hard drives and even to shore-based servers.

Beyond this core functionally OpenVDMv2 includes a plugin architecture allowing vessel operators to install their own code to create simplified datasets for the purposes of visualizing, performing data quality tests and generating file statistics.

OpenVDMv2 also includes full RESTful API, allowing vessel operators to built their own custom web-based and stand-alone applications that leverage information stored within OpenVDMv2 for their own, vessel-specific needs.

For more information on OpenVDMv2 please checkout <http://oceandatarat.org>.

####Demo Site
<http://capablesolutions.dyndns.org:8180/OpenVDMv2/>
- Username: ***admin***
- Password: ***demo***

##Installation
Goto <http://xubuntu.org/getxubuntu/>

Download Xubuntu for your hardware.  At the time of this writing we are using 14.04.3 (32-bit)

Perform the default Xubuntu install.  For these instructions the default account that is created is "Survey" and the computer name is "Warehouse".

A few minutes after the install completes and the computer restarts, Xubuntu will ask to install any updates that have arrived since the install image was created.  Perform these now and do not continue with these instructions until the update has completed.

Before OpenVDMv2 can be installed serveral other services and software packaged must be installed and configured.

###SSH Client/Server
SSH is used thoughout OpenVDM for providing secure communication between the Warehouse and other workstations aboard the vessel.  SSH is also used for OpenVDM's ship-to-shore communications.

To install SSH open a terminal window and type:
```
sudo apt-get install ssh
```

###MySQL Database
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

maybe --> php-pear php5-dev

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

###OpenVDMv2

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
source /home/survey/Downloads/OpenVDMv2-master/OpenVDMv2_db.sql;
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

 - Set the file URL of the OpenVDMv2 installation.  Look for the following lines and change the URL to the actual URL of the installation:
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

Copy text below into the Apache2 configuration file just above `</VirtualHost>`.
```
  Alias /OpenVDMv2 /var/www/OpenVDMv2
  <Directory "/var/www/OpenVDMv2">
    AllowOverride all
  </Directory>
```

Reload Apache2
```
sudo service apache2 reload
```

###Samba
One of the ways OpenVDM communicates with data collection system is through Windows Shares configured on the collection system workstation.  Windows shares are also configured on the data warehouse to allow scientists and crew to easily access data stored on the Warehouse from their Windows or Mac Laptops.  Windows shares on a non-windows machine are made possible thanks to the Samba project.  

To install Samba open a terminal window and type:
`sudo apt-get install samba smbclient`

###Miscellaneous Packages
`sudo apt-get install rsync curl git gdal-bin python-gdal`
maybe --> npm nodejs-legacy

###MapProxy
`apt-get install mapproxy`


gearman

sudo pecl install gearman

###Install Composer
curl-sS https://getcomposer.org/installer | php
mv Composer.phar /usr/local/bin

gdal-bin python-gdal
npm nodejs-legacy
sshpass
