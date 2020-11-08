PREFERENCES_FILE='.install_openvdm_preferences'

###########################################################################
###########################################################################
# Read any pre-saved default variables from file
function set_default_variables {
    # Defaults that will be overwritten by the preferences file, if it
    # exists.
    DEFAULT_HOSTNAME=$HOSTNAME
    DEFAULT_DATA_ROOT=/vault

    DEFAULT_OPENVDM_REPO=https://github.com/webbpinner/OpenVDMv2
    DEFAULT_OPENVDM_BRANCH=v2.3

    DEFAULT_OPENVDM_USER=survey

    # Read in the preferences file, if it exists, to overwrite the defaults.
    if [ -e $PREFERENCES_FILE ]; then
        echo Reading pre-saved defaults from "$PREFERENCES_FILE"
        source $PREFERENCES_FILE
        echo branch $DEFAULT_OPENVDM_BRANCH
    fi
}


###########################################################################
###########################################################################
# Save defaults in a preferences file for the next time we run.
function save_default_variables {
    cat > $PREFERENCES_FILE <<EOF
# Defaults written by/to be read by install_openvdm_ubuntu18.04.sh

DEFAULT_HOSTNAME=$HOSTNAME
DEFAULT_DATA_ROOT=$DATA_ROOT

DEFAULT_OPENVDM_REPO=$OPENVDM_REPO
DEFAULT_OPENVDM_BRANCH=$OPENVDM_BRANCH

DEFAULT_OPENVDM_USER=$OPENVDM_USER
EOF
}


###########################################################################
###########################################################################
# Set hostname
function set_hostname {
    HOSTNAME=$1
    hostnamectl set-hostname $HOSTNAME
    echo $HOSTNAME > /etc/hostname
    ETC_HOSTS_LINE="127.0.1.1   $HOSTNAME"
    if grep -q "$ETC_HOSTS_LINE" /etc/hosts ; then
        echo Hostname already in /etc/hosts
    else
        echo "$ETC_HOSTS_LINE" >> /etc/hosts
    fi
}

###########################################################################
###########################################################################
# Create user
function create_user {
    OPENVDM_USER=$1

    echo Checking if user $OPENVDM_USER exists yet
    if id -u $OPENVDM_USER > /dev/null; then
        echo User exists, skipping
    else
        echo Creating $OPENVDM_USER
        adduser --gecos "" $OPENVDM_USER
        #passwd $OPENVDM_USER
        usermod -a -G tty $OPENVDM_USER
        usermod -a -G sudo $OPENVDM_USER
    fi
}

###########################################################################
###########################################################################
# Install and configure required packages
function install_packages {
    apt-get update

    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/php
    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/apache2
    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/pkg-gearman

    add-apt-repository -y ppa:ubuntugis/ppa

    apt-get update

    apt install -y ssh sshpass rsync samba smbclient gearman-job-server \
        libgearman-dev python-pip curl nodejs nodejs-dev node-gyp npm \
        supervisor mysql-server mysql-client cifs-utils apache2 \
        libapache2-mod-wsgi libapache2-mod-php7.3 php7.3 php7.3-cli \
        php7.3-mysql php7.3-zip gdal-bin php7.3-curl php7.3-gearman \
        php-yaml python-pip python-pil python-yaml libgeos-dev \
        python-gdal python-lxml python-shapely python-requests proj-bin 

    pip install gearman MapProxy pandas geopy

    startingDir=${PWD}

    cd ~
    curl -sS https://getcomposer.org/installer | php
    mv composer.phar /usr/local/bin/composer

    cd ${startingDir}

    npm install -g bower
}


###########################################################################
###########################################################################
# Install and configure database
function configure_supervisor {

    mv /etc/supervisor/supervisord.conf /etc/supervisor/supervisord.conf.orig

    grep -v "\[inet_http_server\]" /etc/supervisor/supervisord.conf.orig | grep -v "port = 9001" > /etc/supervisor/supervisord.conf

    cat >> /etc/supervisor/supervisord.conf <<EOF

[inet_http_server]
port = 9001
EOF

    systemctl restart supervisor.service 

}


###########################################################################
###########################################################################
# Install and configure database
function configure_gearman {
    echo Restarting Gearman Job Server
    service gearman-job-server restart
}


###########################################################################
###########################################################################
# Install and configure database
function configure_samba {

    mv /etc/samba/smb.conf /etc/samba/smb.conf.orig

    sed -e 's/obey pam restrictions = yes/obey pam restrictions = no/' /etc/samba/smb.conf.orig | grep -v "include = /etc/samba/openvdm.conf" > /etc/samba/smb.conf
    cat >> /etc/samba/smb.conf <<EOF

include = /etc/samba/openvdm.conf
EOF

    cat >> /etc/samba/openvdm.conf <<EOF
# SMB Shares for OpenVDM

[CruiseData]
  comment=Cruise Data, read-only access to guest
  path=${DATA_ROOT}/FTPRoot/CruiseData
  browsable = yes
  public = yes
  guest ok = yes
  writable = yes
  write list = ${OPENVDM_USER}
  create mask = 0644
  directory mask = 0755
  veto files = /._*/.DS_Store/.Trashes*/
  delete veto files = yes

[VisitorInformation]
  comment=Visitor Information, read-only access to guest
  path=${DATA_ROOT}/FTPRoot/VisitorInformation
  browsable = yes
  public = yes
  guest ok = yes
  writable = yes
  write list = ${OPENVDM_USER}
  create mask = 0644
  directory mask = 0755
  veto files = /._*/.DS_Store/.Trashes*/
  delete veto files = yes

[PublicData]
  comment=Public Data, read/write access to all
  path=${DATA_ROOT}/FTPRoot/PublicData
  browseable = yes
  public = yes
  guest ok = yes
  writable = yes
  create mask = 0000
  directory mask = 0000
  veto files = /._*/.DS_Store/.Trashes*/
  delete veto files = yes
  force create mode = 666
  force directory mode = 777
EOF

    echo Restarting SMB Server
    systemctl restart smbd.service
}


function configure_apache {

    cat >> ~/openvdm.conf <<EOF
<VirtualHost *:80>
    ServerName $HOSTNAME

    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
    # error, crit, alert, emerg.
    # It is also possible to configure the loglevel for particular
    # modules, e.g.
    #LogLevel info ssl:warn

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined

    # For most configuration files from conf-available/, which are
    # enabled or disabled at a global level, it is possible to
    # include a line for only one particular virtual host. For example the
    # following line enables the CGI configuration for this host only
    # after it has been globally disabled with "a2disconf".
    #Include conf-available/serve-cgi-bin.conf

    WSGIScriptAlias /mapproxy /var/www/mapproxy/config.py

    <Directory /var/www/mapproxy/>
      Order deny,allow
      Allow from all
    </Directory>

    Alias /OpenVDMv2 /var/www/OpenVDMv2
    <Directory "/var/www/OpenVDMv2">
      AllowOverride all
    </Directory>

    <IfModule mod_rewrite.c>
      RewriteEngine on
      RewriteRule ^/$ /OpenVDMv2/ [R]
    </IfModule>

    Alias /CruiseData/ $DATA_ROOT/FTPRoot/CruiseData/
    <Directory "$DATA_ROOT/FTPRoot/CruiseData">
      AllowOverride None
      Options +Indexes -FollowSymLinks +MultiViews
      Order allow,deny
      Allow from all
      Require all granted
    </Directory>
  
    Alias /PublicData/ $DATA_ROOT/FTPRoot/PublicData/
    <Directory "$DATA_ROOT/FTPRoot/PublicData">
      AllowOverride None
      Options +Indexes -FollowSymLinks +MultiViews
      Order allow,deny
      Allow from all
      Require all granted
    </Directory>

    Alias /VisitorInformation/ $DATA_ROOT/FTPRoot/VisitorInformation/
    <Directory "$DATA_ROOT/FTPRoot/VisitorInformation">
      AllowOverride None
      Options +Indexes -FollowSymLinks +MultiViews
      Order allow,deny
      Allow from all
      Require all granted
    </Directory>

</VirtualHost>
EOF

    echo Enabling ReWrite Module
    a2enmod rewrite

    echo Disabling default vhost
    a2dissite 000-default

    echo Building new vhost file
    mv ~/openvdm.conf /etc/apache2/sites-available/

    echo Enabling new vhost
    a2ensite openvdm

    echo Restarting Apache Web Server
    systemctl restart apache2.service

}


###########################################################################
###########################################################################
# Install and configure database
function configure_mapproxy {

    startingDir=${PWD}

    cd ~
    mapproxy-util create -t base-config --force mapproxy

    cat > ~/mapproxy/mapproxy.yaml <<EOF
# -------------------------------
# MapProxy configuration.
# -------------------------------

# Start the following services:
services:
  demo:
  tms:
    use_grid_names: false
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
     num_levels: 11

globals:
EOF

    cp -r ~/mapproxy /var/www/
    mkdir -p /var/www/mapproxy/cache_data
    chmod 777 /var/www/mapproxy/cache_data
    chown -R root:root /var/www/mapproxy

    cd /var/www/mapproxy
    mapproxy-util create -t wsgi-app -f mapproxy.yaml --force config.py

    cd ${startingDir}

}


###########################################################################
###########################################################################
# Install and configure database
function configure_mysql {
    # Expect the following shell variables to be appropriately set:
    # RVDAS_USER - valid userid
    # RVDAS_DATABASE_PASSWORD - current rvdas user MySQL database password
    # NEW_ROOT_DATABASE_PASSWORD - new root password to use for MySQL
    # CURRENT_ROOT_DATABASE_PASSWORD - current root password for MySQL

    echo Enabling MySQL Database Server

    # apt install -y mysql-server mysql-common mysql-client libmysqlclient-dev
    systemctl restart mysql    # to manually start db server
    systemctl enable mysql     # to make it start on boot

    echo Setting up database root user and permissions
    # Verify current root password for mysql
    while true; do
        # Check whether they're right about the current password; need
        # a special case if the password is empty.
        PASS=TRUE
        [ ! -z $CURRENT_ROOT_DATABASE_PASSWORD ] || (mysql -u root  < /dev/null) || PASS=FALSE
        [ -z $CURRENT_ROOT_DATABASE_PASSWORD ] || (mysql -u root -p$CURRENT_ROOT_DATABASE_PASSWORD < /dev/null) || PASS=FALSE
        case $PASS in
            TRUE ) break;;
            * ) echo "Database root password failed";read -p "Current database password for root? (if one exists - hit return if not) " CURRENT_ROOT_DATABASE_PASSWORD;;
        esac
    done

    # Set the new root password
    cat > /tmp/set_pwd <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$NEW_ROOT_DATABASE_PASSWORD';
FLUSH PRIVILEGES;
EOF

    # If there's a current root password
    [ -z $CURRENT_ROOT_DATABASE_PASSWORD ] || mysql -u root -p$CURRENT_ROOT_DATABASE_PASSWORD < /tmp/set_pwd

    # If there's no current root password
    [ ! -z $CURRENT_ROOT_DATABASE_PASSWORD ] || mysql -u root < /tmp/set_pwd
    rm -f /tmp/set_pwd

    # Now do the rest of the 'mysql_safe_installation' stuff
#     mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
# DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
# DELETE FROM mysql.user WHERE User='';
# DELETE FROM mysql.db WHERE Db='test' OR Db='test_%';
# FLUSH PRIVILEGES;
# EOF

    # Start mysql to start up as a service
    update-rc.d mysql defaults

    echo Setting up OpenVDM database user
    mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
drop user if exists '$OPENVDM_USER'@'localhost';
create user '$OPENVDM_USER'@'localhost' identified by '$OPENVDM_DATABASE_PASSWORD';
flush privileges;
\q
EOF
#     mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
# drop user if exists 'test'@'localhost';
# create user 'test'@'localhost' identified by 'test';
# drop user if exists 'rvdas'@'localhost';
# create user '$RVDAS_USER'@'localhost' identified by '$RVDAS_DATABASE_PASSWORD';
# create database if not exists data character set utf8;
# GRANT ALL PRIVILEGES ON data.* TO '$RVDAS_USER'@'localhost';
# create database if not exists test character set utf8;
# GRANT ALL PRIVILEGES ON test.* TO '$RVDAS_USER'@'localhost';
# GRANT ALL PRIVILEGES ON test.* TO 'test'@'localhost' identified by 'test';
# flush privileges;
# \q
# EOF
    echo Done setting up MySQL
}


function configure_directories {

    if [ ! -d $DATA_ROOT ]; then
      while true; do
        read -p "Root data directory ${DATA_ROOT} does not exists... create it? (yes) " yn
        case $yn in
          [Yy]* )
            mkdir -p ${DATA_ROOT}
            break;;
          "" )
            mkdir -p ${DATA_ROOT}
            break;;
          [Nn]* )
            echo "Quitting"
            exit;;
          * ) echo "Please answer yes or no.";;
        esac
      done
    fi

    if [ ! -d $DATA_ROOT/FTPROOT ]; then
      echo Making data directories starting at: "$DATA_ROOT"
      mkdir -p ${DATA_ROOT}/FTPRoot/CruiseData/Test_Cruise

      mkdir -p ${DATA_ROOT}/FTPRoot/PublicData
      chmod -R 777 ${DATA_ROOT}/FTPRoot/PublicData

      mkdir -p ${DATA_ROOT}/FTPRoot/VisitorInformation

      chown -R ${OPENVDM_USER}:${OPENVDM_USER} $DATA_ROOT/FTPRoot/*

    fi

    if [ ! -d  /var/log/OpenVDM ]; then
      mkdir /var/log/OpenVDM
    fi

}


###########################################################################
###########################################################################
# Install OpenRVDAS
function install_openvdm {
    # Expect the following shell variables to be appropriately set:
    # DATA_ROOT - path where data will be stored is
    # OPENVDM_USER - valid userid
    # OPENVDM_REPO - path to OpenVDM repo
    # OPENVDM_BRANCH - branch of rep to install

    startingDir=${PWD}
    cd ~/

    if [ ! -e OpenVDMv2 ]; then  # New install
      echo Downloading OpenVDMv2 repository.
      git clone -b $OPENVDM_BRANCH $OPENVDM_REPO
      chown ${OPENVDM_USER}:${OPENVDM_USER} OpenVDMv2

    else
      cd OpenVDMv2

      if [ -e .git ] ; then   # If we've already got an installation
        echo Updating existing OpenVDMv2 repository.
        git pull
        git checkout $OPENVDM_BRANCH
        git pull
        cd ..

      else
        echo Downloading OpenVDMv2 repository.  # Bad install, re-doing
        cd ..
        rm -rf OpenVDMv2
        git clone -b $OPENVDM_BRANCH $OPENVDM_REPO
      fi
    fi

    cd ~/OpenVDMv2

    DB_EXISTS=`mysqlshow --user=root --password=${NEW_ROOT_DATABASE_PASSWORD} OpenVDMv2| grep -v Wildcard`
    if [ $? == 0 ]; then
      echo OpenVDMv2 database found, skipping database setup
      mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
GRANT ALL PRIVILEGES ON OpenVDMv2.* TO '$OPENVDM_USER'@'localhost';
flush privileges;
\q
EOF

    else
      echo Setup OpenVDMv2 database
      sed -e "s|/vault/FTPRoot|${DATA_ROOT}/FTPRoot|" ./OpenVDMv2_db.sql | \
      sed -e "s/survey/${OPENVDM_USER}/" | \
      sed -e "s/127\.0\.0\.1/${HOSTNAME}/" \
      > ./OpenVDMv2_db_custom.sql

      mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
create database if not exists OpenVDMv2 character set utf8;
GRANT ALL PRIVILEGES ON OpenVDMv2.* TO '$OPENVDM_USER'@'localhost';
USE OpenVDMv2;
source ./OpenVDMv2_db_custom.sql;
flush privileges;
\q
EOF
    fi

    echo Building web-app
    cd ./var/www/OpenVDMv2
    composer -q install
    cd ../../../

    echo Installing web-app
    rsync -a ./var/www/OpenVDMv2 /var/www/
    cp /var/www/OpenVDMv2/.htaccess.dist /var/www/OpenVDMv2/.htaccess
    
    sed -s "s/define('DB_USER', 'openvdmDBUser');/define('DB_USER', ${OPENVDM_USER});/" /var/www/OpenVDMv2/app/Core/Config.php.dist | \
    sed -e "s/define('DB_PASS', 'oxhzbeY8WzgBL3');/define('DB_PASS', ${OPENVDM_DATABASE_PASSWORD});/" \
    > /var/www/OpenVDMv2/app/Core/Config.php
    
    touch /var/www/OpenVDMv2/errorlog.html
    chmod 777 /var/www/OpenVDMv2/errorlog.html
    chown -R root:root /var/www/OpenVDMv2

    echo Installing configuration files
    mkdir -p /usr/local/etc/openvdm
    rsync -a ./usr/local/etc/openvdm/* /usr/local/etc/openvdm/
    cp /usr/local/etc/openvdm/datadashboard.yaml.dist /usr/local/etc/openvdm/datadashboard.yaml
    cat /usr/local/etc/openvdm/openvdm.yaml.dist | sed -e "s/127.0.0.1/${HOSTNAME}/" > /usr/local/etc/openvdm/openvdm.yaml

    echo Installing executables
    rsync -a ./usr/local/bin/* /usr/local/bin/

    echo Configuring Supervisor processes
    rsync -a ./etc/supervisor/conf.d/* /etc/supervisor/conf.d/
    mv /etc/supervisor/conf.d/OVDM_runCollectionSystemTransfer.conf.dist /etc/supervisor/conf.d/OVDM_runCollectionSystemTransfer.conf
    mv /etc/supervisor/conf.d/OVDM_postCollectionSystemTransfer.conf.dist /etc/supervisor/conf.d/OVDM_postCollectionSystemTransfer.conf

    cd ${startingDir}

    echo Restarting Supervisor
    systemctl restart supervisor.service

}


###########################################################################
###########################################################################
###########################################################################
###########################################################################
# Start of actual script
###########################################################################
###########################################################################

# Read from the preferences file in $PREFERENCES_FILE, if it exists
set_default_variables

if [ "$(whoami)" != "root" ]; then
  echo "ERROR: installation script must be run as root."
  return -1 2> /dev/null || exit -1  # terminate correctly if sourced/bashed
fi


echo "#####################################################################"
echo OpenVDM configuration script

echo "#####################################################################"
read -p "Name to assign to host ($DEFAULT_HOSTNAME)? " HOSTNAME
HOSTNAME=${HOSTNAME:-$DEFAULT_HOSTNAME}
echo "Hostname will be '$HOSTNAME'"

# Set hostname
set_hostname $HOSTNAME

read -p "Repository to install from? ($DEFAULT_OPENVDM_REPO) " OPENVDM_REPO
OPENVDM_REPO=${OPENVDM_REPO:-$DEFAULT_OPENVDM_REPO}

read -p "Repository branch to install? ($DEFAULT_OPENVDM_BRANCH) " OPENVDM_BRANCH
OPENVDM_BRANCH=${OPENVDM_BRANCH:-$DEFAULT_OPENVDM_BRANCH}

echo Will install from github.com
echo "Repository: '$OPENVDM_REPO'"
echo "Branch: '$OPENVDM_BRANCH'"
echo

# Create user if they don't exist yet
echo "#####################################################################"
read -p "OpenVDM user to create? ($DEFAULT_OPENVDM_USER) " OPENVDM_USER
OPENVDM_USER=${OPENVDM_USER:-$DEFAULT_OPENVDM_USER}
create_user $OPENVDM_USER

echo
read -p "OpenVDMv2 Database password to use for user $OPENVDM_USER? ($OPENVDM_USER) " OPENVDM_DATABASE_PASSWORD
OPENVDM_DATABASE_PASSWORD=${OPENVDM_DATABASE_PASSWORD:-$OPENVDM_USER}

echo Will install/configure MySQL
# Get current and new passwords for database
echo Root database password will be empty on initial installation. If this
echo is the initial installation, hit "return" when prompted for root
echo database password, otherwise enter the password you used during the
echo initial installation.
echo
echo Current database password for root \(hit return if this is the
read -p "initial installation)? " CURRENT_ROOT_DATABASE_PASSWORD
read -p "New database password for root? ($CURRENT_ROOT_DATABASE_PASSWORD) " NEW_ROOT_DATABASE_PASSWORD
NEW_ROOT_DATABASE_PASSWORD=${NEW_ROOT_DATABASE_PASSWORD:-$CURRENT_ROOT_DATABASE_PASSWORD}

read -p "Root data directory for OpenVDM? ($DEFAULT_DATA_ROOT) " DATA_ROOT
DATA_ROOT=${DATA_ROOT:-$DEFAULT_DATA_ROOT}

#########################################################################
#########################################################################
# Save defaults in a preferences file for the next time we run.
save_default_variables

#########################################################################
#########################################################################
# Install packages
echo "#####################################################################"
echo Installing required software packages and libraries
install_packages

echo "#####################################################################"
echo Creating required directories
configure_directories

echo "#####################################################################"
echo Configuring gearman-job-server
configure_gearman

echo "#####################################################################"
echo Configuring MySQL
configure_mysql

echo "#####################################################################"
echo Configuring Supervisor
configure_supervisor

echo "#####################################################################"
echo Installing/Configuring OpenVDM
install_openvdm

echo "#####################################################################"
echo Configuring Samba
configure_samba

echo "#####################################################################"
echo Installing/Configuring MapProxy
configure_mapproxy

echo "#####################################################################"
echo Configuring Apache2
configure_apache

#########################################################################
#########################################################################
