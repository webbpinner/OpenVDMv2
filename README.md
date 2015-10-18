[OpenVDMv2_Logo]: http://www.oceandatarat.org/wp-content/uploads/2014/11/openVDM_LogoV2_1_long.png "Open Vessel Data Managment v2" 

![OpenVDMv2_Logo]
#Open Vessel Data Management v2

##Installation
Goto <http://xubuntu.org/getxubuntu/>

Download Xubuntu for your hardware.  At the time of this writing we are using 14.04.3 (32-bit)

Perform the default Xubuntu install.  For these instructions the default account that is created is "Survey" and the computer name is "Warehouse".

A few minutes after the install completes and the computer restarts, Xubuntu will ask to install any updates that have arrived since the install image was created.  Perform these now and do not continue with these instructions until the update has completed.

###Download the OpenVDM Files from Github

All of the files needed to run OpenVDMv2 including the example configuration files are avaiable for download from GitHub as a single compressed archive (zip file).

To download the zip file from GitHub, goto the OpenVDM GitHub page: <https://github.com/webbpinner/OpenVDMv2> and click the "Download Zip" button.  This should place the zip file in the Downloads folder for the default account.

Double-click on the zip file to uncompress the file.

As the services required by OpenVDM are installed the files contained within this directory structure will be used to configure those services to work with OpenVDM.

From a terminal window:
```
curl https://github.com/webbpinner/OpenVDMv2/archive/master.zip
```

###SSH Client/Server
SSH is used thoughout OpenVDM for providing secure communication between the Warehouse and other workstations aboard the vessel.  SSH is also used for OpenVDM's ship-to-shore communications.

To install SSH open a terminal window and type:
`sudo apt-get install ssh`

###MySQL Database
All of the commonly used variables, tranfer profiles, and user creditials for OpenVDM are stored in a SQL database.  This allows fast access to the stored information as well as a proven mechanism for multiple clients to change records without worry of write collisions.  OpenVDM uses the MySQL open-source database server.

To install MySQL open a terminal window and type:
```
sudo apt-get install mysql-server
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
  
###PHP5
The language used to write the OpenVDMv2 web-interface is PHP.

To install PHP open a terminal window and type:
```
sudo apt-get install php5 php5-cli php5-mysql
```

maybe --> php-pear php5-dev

###Gearman and Supervisor
Behind the OpenVDM web-application are several background processes that perform the various data transfers and other tasks.  Managing these background processes is a job broker and processes manager.

The job broker listens for requests to perform a specific task.  Once a request has arrived, the job broker farms the task out to the next available process that can perform that specific task.  OpenVDM uses Gearman as it's job broker.

Making sure the right type and number of worker processes are available to Gearman is the role of the process manager.  OpenVDM uses Supervisor as it's process manager.

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

OpenVDM requires that php5 be integrated with Gearman. To do that add `extension=gearman.so` to `/etc/php5/cli/php`.  This will require root privledges:

`sudo nano /etc/php5/cli/php.ini`

Also add `extension=gearman.so` to `/etc/php5/apache2/php`.  This will also require root privledges:

`sudo nano /etc/php5/apache2/php.ini`

Restart Apache
`service apache2 restart`

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

###Gearman-UI
Gearman-UI is not directly part of OpenVDM or the Gearman job broker however it is extremely useful when troubleshooting problems with Gearman.

####Installing composer

From a terminal window type:
```
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
```

####Install bower
```
sudo apt-get install npm nodejs-legacy
npm install -g bower
```
####Install Gearman-UI
```
curl https://github.com/gaspaio/gearmanui/archive/master.zip
unzip master.zip
cd gearman-ui
composer install --no-dev
bower install
cp config.yml.dist config.yml
cd ..
sudo mv gearman-ui /usr/local/share/
```

Create a new Apache VHost file.
```
sudo nano /etc/apache2/sites-available/gearman.conf
```

Copy text below into the new configuration file.
```
<VirtualHost *:80>
  DocumentRoot /usr/local/gearman-ui
  #ServerName www.example.com
  ServerPath /gearman-ui/
</VirtualHost>
```

Enable the site and reload Apache2
```
sudo a2ensite gearman-ui
sudo service apache2 reload
```

Verify the installation was successful by going to: <http://127.0.0.1/gearman-ui>

###Install OpenVDMv2 Web-Application

Before the OpenVDMv2 web-application will work, two configuration files must be modified to match the configuration of the Warehouse.  This includes setting the URL from where users will access the OpenVDM web-application and database access credentials.  

By default the github zip file does not include these file but rather 2 example files that must be copied, renamed and modified.  This approach is used to simplify future upgrade.

The two requried configuration files are `.htaccess` and `./app/Core/Config.php` (relative to the ./var/www/html/OpenVDMv2 folder).  The example files provided are in the same locations as where the actual configuration files need to be located and simply include a `.example` suffix.

Create the actual configuration files by either copy/paste/rename the files in the file manager window or from a terminal window:
```
cd /home/survey/Downloads/OpenVDMv2-master/var/www/html/OpenVDMv2
cp ./.htaccess.example ./.htaccess
cp ./app/Core/Config.php.example ./app/Core/Config.php
```

Changes that must be made to `.htaccess`
 - Set the `RewriteBase` to part of the URL after the hostname that will become the landing page for OpenVDMv2.  By default this is set to `OpenVDMv2` meaning that once active users will go to http://<hostname or IP>/OpenVDMv2/.

Changes that must be made to `./app/Core/Config.php`
 - Set the file URL of the OpenVDMv2 installation.  Look for the following lines and change the URL to the actual URL of the installation:
```
//site address
define('DIR', 'http://127.0.0.1/OpenVDMv2/');
```

A word of caution. The framework used by OpenVDMv2 does not allow more than one URL to access the web-application.  This means that you can NOT access the web-application using the machine hostname AND IP.  You must pick one.  Also with dual-homed machines you CAN NOT access the web-application by entering the IP address of the interface not used in this configuration file.  Typically this is not a problem since dual-homed installation are dual-homed because the Warehouse is spanning a public and private subnet.  While users on the the public subnet can't access machines on the private network, users on the private network can access machines on the public network.  In that scenario the URL should be set to the Warehouse's interface on the public network, thus allowing users on both subnets access.

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

Once the configuration files have been modified, copy the ./var/www/html/OpenVDMv2 directory from the GitHub zipfile extract to the /var/www/html folder on the Ware house.  Because of file/folder permissions, this must be done from a terminal window.  Within a terminal window open, type:
```
sudo cp -r ~/Downloads/OpenVDMv2-master/var/www/html/OpenVDMv2 /var/www/html/
sudo chmod 777 /var/www/html/OpenVDMv2/errorlog.html
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
