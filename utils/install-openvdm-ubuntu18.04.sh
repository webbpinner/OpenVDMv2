#!/bin/bash -e

# OpenVDM is available as open source under the GPLv3 License at
#   https:/github.com/webbpinner/OpenVDMv2
#
# This script installs and configures OpenVDM to run on Ubuntu 20.04.  It
# is designed to be run as root. It should take a (relatively) clean
# Ubuntu 20.04 installation and install and configure all the components
# to run the full OpenVDM system.
#
# It should be re-run whenever the code has been refresh. Preferably
# by first running 'git pull' to get the latest copy of the script,
# and then running 'utils/build_openvdm_ubuntu20.04.sh' to run that
# script.
#
# The script has been designed to be idempotent, that is, if can be
# run over again with no ill effects.
#
# This script is somewhat rudimentary and has not been extensively
# tested. If it fails on some part of the installation, there is no
# guarantee that fixing the specific issue and simply re-running will
# produce the desired result.  Bug reports, and even better, bug
# fixes, will be greatly appreciated.


PREFERENCES_FILE='.install_openvdm_preferences'

###########################################################################
###########################################################################
function exit_gracefully {
    echo Exiting.

    # Try deactivating virtual environment, if it's active
    if [ -n "$INSTALL_ROOT" ];then
        deactivate
    fi
    return -1 2> /dev/null || exit -1  # exit correctly if sourced/bashed
}

#########################################################################
#########################################################################
# Return a normalized yes/no for a value
yes_no() {
    QUESTION=$1
    DEFAULT_ANSWER=$2

    while true; do
        read -p "$QUESTION ($DEFAULT_ANSWER) " yn
        case $yn in
            [Yy]* )
                YES_NO_RESULT=yes
                break;;
            [Nn]* )
                YES_NO_RESULT=no
                break;;
            "" )
                YES_NO_RESULT=$DEFAULT_ANSWER
                break;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

###########################################################################
###########################################################################
# Read any pre-saved default variables from file
function set_default_variables {
    # Defaults that will be overwritten by the preferences file, if it
    # exists.
    DEFAULT_HOSTNAME=$HOSTNAME
    DEFAULT_INSTALL_ROOT=/opt

    DEFAULT_DATA_ROOT=/vault

    DEFAULT_OPENVDM_REPO=https://github.com/webbpinner/OpenVDMv2
    DEFAULT_OPENVDM_BRANCH=v2.5

    DEFAULT_OPENVDM_USER=survey

    DEFAULT_SUPERVISORD_WEBINTERFACE=no
    DEFAULT_SUPERVISORD_WEBINTERFACE_AUTH=no
    DEFAULT_SUPERVISORD_WEBINTERFACE_PORT=9001

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
# Defaults written by/to be read by install_openvdm_ubuntu20.04.sh

DEFAULT_HOSTNAME=$HOSTNAME
DEFAULT_INSTALL_ROOT=$INSTALL_ROOT

DEFAULT_DATA_ROOT=$DATA_ROOT

DEFAULT_OPENVDM_REPO=$OPENVDM_REPO
DEFAULT_OPENVDM_BRANCH=$OPENVDM_BRANCH

DEFAULT_OPENVDM_USER=$OPENVDM_USER

DEFAULT_SUPERVISORD_WEBINTERFACE=$SUPERVISORD_WEBINTERFACE
DEFAULT_SUPERVISORD_WEBINTERFACE_AUTH=$SUPERVISORD_WEBINTERFACE_AUTH
DEFAULT_SUPERVISORD_WEBINTERFACE_PORT=$SUPERVISORD_WEBINTERFACE_PORT

EOF
}


###########################################################################
###########################################################################
# Set hostname
function set_hostname {
    HOSTNAME=$1

    hostnamectl set-hostname $HOSTNAME
    echo $HOSTNAME > /etc/hostname

    ETC_HOSTS_LINE="127.0.1.1 $HOSTNAME"
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

    echo "Checking if user $OPENVDM_USER exists yet"
    if id -u $OPENVDM_USER > /dev/null; then
        echo User exists, skipping
        return
    fi

    echo "Creating $OPENVDM_USER"
    adduser --gecos "" $OPENVDM_USER
    usermod -a -G sudo $OPENVDM_USER
}

###########################################################################
###########################################################################
# Install and configure required packages
function install_packages {

    apt-get update

    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/php
    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/apache2
    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/pkg-gearman

    # add-apt-repository -y ppa:ubuntugis/ppa

    apt-get update

    apt install -y openssh-server sshpass rsync curl git samba smbclient \
        cifs-utils gearman-job-server libgearman-dev nodejs libnode-dev \
        node-gyp npm python3 python3-dev python3-pip python3-venv libgdal-dev \
        gdal-bin libgeos-dev supervisor mysql-server mysql-client ntp \
        apache2 libapache2-mod-wsgi-py3 libapache2-mod-php7.3 php7.3 php7.3-cli \
        php7.3-mysql php7.3-zip php7.3-curl php7.3-gearman php7.3-yaml proj-bin \
	    python3-pyproj

    pip3 install MapProxy
    
    # TODO Install these via virtualenv
    #python-pip python-pip python-pil python-gdal python-lxml python-shapely python-requests

    # pip install python3_gearman pandas geopy gdal pyyaml requests

    # change from cgi import escape to from html import escape in 
    # /usr/lib/python3/dist-packages/mapproxy/service/template_helper.py 
    # (line 16)

    npm install -g bower

    startingDir=${PWD}

    cd ~
    curl -sS https://getcomposer.org/installer | php
    mv composer.phar /usr/local/bin/composer

    cd ${startingDir}
}


###########################################################################
###########################################################################
# Set up Python packages
function install_python_packages {
    # Expect the following shell variables to be appropriately set:
    # INSTALL_ROOT - path where openvdm is

    # Set up virtual environment
    VENV_PATH=$INSTALL_ROOT/openvdm/venv
    python3 -m venv $VENV_PATH
    source $VENV_PATH/bin/activate  # activate virtual environment

    pip install \
      --trusted-host pypi.org --trusted-host files.pythonhosted.org \
      --upgrade pip
    pip install wheel  # To help with the rest of the installations

    pip install -r $INSTALL_ROOT/openvdm/requirements.txt

    pip install --global-option=build_ext --global-option="-I/usr/include/gdal" GDAL==`gdal-config --version`
}


###########################################################################
###########################################################################
# Install and configure database
function configure_supervisor {

    mv /etc/supervisor/supervisord.conf /etc/supervisor/supervisord.conf.orig

    sed -e '/### Added by OpenVDM install script ###/,/### Added by OpenVDM install script ###/d' /etc/supervisor/supervisord.conf.orig |
    sed -e :a -e '/^\n*$/{$d;N;};/\n$/ba' > /etc/supervisor/supervisord.conf

    if [ $SUPERVISORD_WEBINTERFACE == 'yes' ]; then
        cat >> /etc/supervisor/supervisord.conf <<EOF

### Added by OpenVDM install script ###
[inet_http_server]
port=9001
EOF
        if [ $SUPERVISORD_WEBINTERFACE_AUTH == 'yes' ]; then
            SUPERVISORD_WEBINTERFACE_HASH=`echo -n ${SUPERVISORD_WEBINTERFACE_PASS} | sha1sum | awk '{printf("{SHA}%s",$1)}'`
            cat >> /etc/supervisor/supervisord.conf <<EOF
username=${SUPERVISORD_WEBINTERFACE_USER}
password=${SUPERVISORD_WEBINTERFACE_HASH} ; echo -n "<password>" | sha1sum | awk '{printf("{SHA}%s",\$1)}'
EOF
        fi

      cat >> /etc/supervisor/supervisord.conf <<EOF
### Added by OpenVDM install script ###
EOF
    fi

VENV_BIN=${INSTALL_ROOT}/openvdm/venv/bin

    cat > /etc/supervisor/conf.d/openvdm.conf << EOF
[program:cruise]
command=${VENV_BIN}/python server/workers/cruise.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/cruise.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:cruise_directory]
command=${VENV_BIN}/python server/workers/cruise_directory.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/cruiseDirectory.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:data_dashboard]
command=${VENV_BIN}/python server/workers/data_dashboard.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/dataDashboard.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:lowering]
command=${VENV_BIN}/python server/workers/lowering.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/lowering.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:lowering_directory]
command=${VENV_BIN}/python server/workers/lowering_directory.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/lowering_directory.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:md5_summary]
command=${VENV_BIN}/python server/workers/md5_summary.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/md5_summary.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:post_hooks]
command=${VENV_BIN}/python server/workers/post_hooks.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/post_hooks.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:reboot_reset]
command=${VENV_BIN}/python server/workers/reboot_reset.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/reboot_reset.log
user=root
autostart=true
autorestart=false
stopsignal=INT

[program:run_collection_system_transfer]
command=${VENV_BIN}/python server/workers/run_collection_system_transfer.py
directory=${INSTALL_ROOT}/openvdm
process_name=%(program_name)s_%(process_num)s
numprocs=2
redirect_stderr=true
stdout_logfile=/var/log/openvdm/run_collection_system_transfer.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:run_cruise_data_transfer]
command=${VENV_BIN}/python server/workers/run_cruise_data_transfer.py
directory=${INSTALL_ROOT}/openvdm
process_name=%(program_name)s_%(process_num)s
numprocs=2
redirect_stderr=true
stdout_logfile=/var/log/openvdm/run_cruise_data_transfer.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:run_ship_to_shore_transfer]
command=${VENV_BIN}/python server/workers/run_ship_to_shore_transfer.py
directory=${INSTALL_ROOT}/openvdm
process_name=%(program_name)s_%(process_num)s
numprocs=2
redirect_stderr=true
stdout_logfile=/var/log/openvdm/run_ship_to_shore_transfer.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:scheduler]
command=${VENV_BIN}/python server/workers/scheduler.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/scheduler.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:size_cacher]
command=${VENV_BIN}/python server/workers/size_cacher.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/size_cacher.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:stop_job]
command=${VENV_BIN}/python server/workers/stop_job.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/stop_job.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:test_collection_system_transfer]
command=${VENV_BIN}/python server/workers/test_collection_system_transfer.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/test_collection_system_transfer.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[program:test_cruise_data_transfer]
command=${VENV_BIN}/python server/workers/test_cruise_data_transfer.py
directory=${INSTALL_ROOT}/openvdm
redirect_stderr=true
stdout_logfile=/var/log/openvdm/test_cruise_data_transfer.log
user=root
autostart=true
autorestart=true
stopsignal=INT

[group:openvdm]
programs=cruise,cruise_directory,data_dashboard,lowering,lowering_directory,md5_summary,post_hooks,reboot_reset,run_collection_system_transfer,run_cruise_data_transfer,run_ship_to_shore_transfer,scheduler,size_cacher,stop_job,test_collection_system_transfer,test_cruise_data_transfer

EOF
    echo "Starting new supervisor processes"
    supervisorctl reread
    systemctl restart supervisor.service
    
}


###########################################################################
###########################################################################
# Install and configure database
function configure_gearman {
    echo "Restarting Gearman Job Server"
    service gearman-job-server restart
}


###########################################################################
###########################################################################
# Install and configure database
function configure_samba {

    echo "Set smbpasswd for ${OPENVDM_USER}, recommended to use same password as system user"
    smbpasswd -a ${OPENVDM_USER}

    mv /etc/samba/smb.conf /etc/samba/smb.conf.orig

    sed -e 's/obey pam restrictions = yes/obey pam restrictions = no/' /etc/samba/smb.conf.orig |
    sed -e '/### Added by OpenVDM install script ###/,/### Added by OpenVDM install script ###/d' |
    sed -e :a -e '/^\n*$/{$d;N;};/\n$/ba'  > /etc/samba/smb.conf
    
    cat >> /etc/samba/smb.conf <<EOF

/### Added by OpenVDM install script ###
include = /etc/samba/openvdm.conf
/### Added by OpenVDM install script ###
EOF

    cat > /etc/samba/openvdm.conf <<EOF
# SMB Shares for OpenVDM

[CruiseData]
  comment=Cruise Data, read-only access to guest
  path=${DATA_ROOT}/FTPRoot/CruiseData
  browsable = yes
  public = yes
  hide unreadable = yes
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

    echo "Restarting Samba Service"
    systemctl restart smbd.service
}


function configure_apache {

    echo "Building new vhost file"
    cat > /etc/apache2/sites-available/openvdm.conf <<EOF
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

    echo "Enabling ReWrite Module"
    a2enmod rewrite

    echo "Disabling default vhost"
    a2dissite 000-default

    echo "Enabling new vhost"
    a2ensite openvdm

    echo "Restarting Apache Web Server"
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

    # sed -e "s|cgi import|html import|" /usr/lib/python3/dist-packages/mapproxy/service/template_helper.py > /usr/lib/python3/dist-packages/mapproxy/service/template_helper.py
    cd ${startingDir}

}


###########################################################################
###########################################################################
# Install and configure database
function configure_mysql {
    # Expect the following shell variables to be appropriately set:
    # OPENVDM_USER - valid userid
    # OPENVDM_DATABASE_PASSWORD - current OpenVDM user MySQL database password
    # NEW_ROOT_DATABASE_PASSWORD - new root password to use for MySQL
    # CURRENT_ROOT_DATABASE_PASSWORD - current root password for MySQL

    echo "Enabling MySQL Database Server"

    systemctl restart mysql    # to manually start db server
    systemctl enable mysql     # to make it start on boot

    echo "Setting up database root user and permissions"
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

    echo "Setting up OpenVDM database user"
    mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
drop user if exists '$OPENVDM_USER'@'localhost';
create user '$OPENVDM_USER'@'localhost' IDENTIFIED WITH mysql_native_password BY '$OPENVDM_DATABASE_PASSWORD';
flush privileges;
\q
EOF
    echo "Done setting up MySQL"
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
                    exit_gracefully;;
                * ) echo "Please answer yes or no.";;
            esac
        done
    fi

    if [ ! -d $DATA_ROOT/FTPROOT ]; then
        echo "Creating data directory structure starting at: $DATA_ROOT"

        mkdir -p ${DATA_ROOT}/FTPRoot/CruiseData/Test_Cruise/Vehicle/Test_Lowering
        mkdir -p ${DATA_ROOT}/FTPRoot/PublicData
        mkdir -p ${DATA_ROOT}/FTPRoot/VisitorInformation

        chmod -R 777 ${DATA_ROOT}/FTPRoot/PublicData
        chown -R ${OPENVDM_USER}:${OPENVDM_USER} $DATA_ROOT/FTPRoot/*
    fi

    if [ ! -d  /var/log/openvdm ]; then
        "Creating logfile directory"
        mkdir -p /var/log/openvdm
    fi

}


###########################################################################
###########################################################################
# Set system timezone
function setup_timezone {
    echo "Etc/UTC" | tee /etc/timezone
    dpkg-reconfigure --frontend noninteractive tzdata
}


###########################################################################
###########################################################################
# Set system ssh
function setup_ssh {

    if [ ! -e ~/.ssh/id_rsa.pub ]; then
        cat /dev/zero | ssh-keygen -q -N "" > /dev/null
        cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    fi

    if [ ! -e /home/${OPENVDM_USER}/.ssh/authorized_keys ]; then
        mkdir -p /home/${OPENVDM_USER}/.ssh
        cat ~/.ssh/id_rsa.pub >> /home/${OPENVDM_USER}/.ssh/authorized_keys
    
        chown -R ${OPENVDM_USER}:${OPENVDM_USER} /home/${OPENVDM_USER}/.ssh
        chmod 600 /home/${OPENVDM_USER}/.ssh/authorized_keys
    fi

    ssh ${OPENVDM_USER}@${HOSTNAME} ls > /dev/null
}


###########################################################################
###########################################################################
# Install OpenVDM
function install_openvdm {
    # Expect the following shell variables to be appropriately set:
    # DATA_ROOT - path where data will be stored is
    # OPENVDM_USER - valid userid
    # OPENVDM_REPO - path to OpenVDM repo
    # OPENVDM_BRANCH - branch of rep to install

    startingDir=${PWD}

    if [ ! -d ${INSTALL_ROOT}/openvdm ]; then  # New install
        echo "Downloading OpenVDMv2 repository"
        cd $INSTALL_ROOT
        git clone -b $OPENVDM_BRANCH $OPENVDM_REPO ./openvdm
        chown ${OPENVDM_USER}:${OPENVDM_USER} ./openvdm

    else
        cd ${INSTALL_ROOT}/openvdm

        if [ -e .git ] ; then   # If we've already got an installation
            echo "Updating existing OpenVDMv2 repository"
            git pull
            git checkout $OPENVDM_BRANCH
            git pull

        else
            echo "Reinstalling OpenVDMv2 from repository"  # Bad install, re-doing
            cd ..
            rm -rf openvdm
            git clone -b $OPENVDM_BRANCH $OPENVDM_REPO ./openvdm
        fi
    fi

    cd ${INSTALL_ROOT}/openvdm

    DB_EXISTS=`mysqlshow --user=root --password=${NEW_ROOT_DATABASE_PASSWORD} OpenVDMv2| grep -v Wildcard`
    if [ $? == 0 ]; then
        echo "OpenVDMv2 database found, skipping database setup"
        mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
GRANT ALL PRIVILEGES ON OpenVDMv2.* TO '$OPENVDM_USER'@'localhost';
flush privileges;
\q
EOF

    else
        echo "Setup OpenVDMv2 database"
        sed -e "s|/vault/FTPRoot|${DATA_ROOT}/FTPRoot|" ${INSTALL_ROOT}/openvdm/database/OpenVDMv2_db.sql | \
        sed -e "s/survey/${OPENVDM_USER}/" | \
        sed -e "s/127\.0\.0\.1/${HOSTNAME}/" \
        > ${INSTALL_ROOT}/openvdm/database/OpenVDMv2_db_custom.sql

        mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
create database if not exists OpenVDMv2 character set utf8;
GRANT ALL PRIVILEGES ON OpenVDMv2.* TO '$OPENVDM_USER'@'localhost';
USE OpenVDMv2;
source ./database/OpenVDMv2_db_custom.sql;
flush privileges;
\q
EOF
    fi

    echo "Building web-app"
    cd ${INSTALL_ROOT}/openvdm/www
    composer -q install


    if [ ! -e ${INSTALL_ROOT}/openvdm/www/.htaccess ] ; then
        cp ${INSTALL_ROOT}/openvdm/www/.htaccess.dist ${INSTALL_ROOT}/openvdm/www/.htaccess
    fi

    if [ ! -e ${INSTALL_ROOT}/openvdm/www/etc/datadashboard.yaml ] ; then
        cp ${INSTALL_ROOT}/openvdm/www/etc/datadashboard.yaml.dist ${INSTALL_ROOT}/openvdm/www/etc/datadashboard.yaml
    fi

    if [ ! -e ${INSTALL_ROOT}/openvdm/www/app/Core/Config.php ] ; then
        sed -s "s/define('DB_USER', 'openvdmDBUser');/define('DB_USER', '${OPENVDM_USER}');/" ${INSTALL_ROOT}/openvdm/www/app/Core/Config.php.dist | \
        sed -e "s/define('DB_PASS', 'oxhzbeY8WzgBL3');/define('DB_PASS', '${OPENVDM_DATABASE_PASSWORD}');/" \
        > ${INSTALL_ROOT}/openvdm/www/app/Core/Config.php
    fi    

    if [ -e ${INSTALL_ROOT}/openvdm/www/errorlog.html ] ; then
        rm ${INSTALL_ROOT}/openvdm/www/errorlog.html
    fi

    touch ${INSTALL_ROOT}/openvdm/www/errorlog.html
    chmod 777 ${INSTALL_ROOT}/openvdm/www/errorlog.html
    chown -R root:root ${INSTALL_ROOT}/openvdm/www

    echo "Installing web-app"
    ln -s ${INSTALL_ROOT}/openvdm/www /var/www/OpenVDMv2

    if [ ! -e ${INSTALL_ROOT}/openvdm/server/etc/openvdm.yaml ] ; then
        echo "Building server configuration file"
        cat ${INSTALL_ROOT}/openvdm/server/etc/openvdm.yaml.dist | sed -e "s/127.0.0.1/${HOSTNAME}/" > ${INSTALL_ROOT}/openvdm/server/etc/openvdm.yaml
    fi

    cd ${startingDir}
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
    exit_gracefully
fi


echo "#####################################################################"
echo "OpenVDM configuration script"

echo "#####################################################################"
read -p "Name to assign to host ($DEFAULT_HOSTNAME)? " HOSTNAME
HOSTNAME=${HOSTNAME:-$DEFAULT_HOSTNAME}
echo "Hostname will be '$HOSTNAME'"
# Set hostname
set_hostname $HOSTNAME
echo

read -p "OpenVDM install root? ($DEFAULT_INSTALL_ROOT) " INSTALL_ROOT
INSTALL_ROOT=${INSTALL_ROOT:-$DEFAULT_INSTALL_ROOT}
echo "Install root will be '$INSTALL_ROOT'"
echo

read -p "Repository to install from? ($DEFAULT_OPENVDM_REPO) " OPENVDM_REPO
OPENVDM_REPO=${OPENVDM_REPO:-$DEFAULT_OPENVDM_REPO}

read -p "Repository branch to install? ($DEFAULT_OPENVDM_BRANCH) " OPENVDM_BRANCH
OPENVDM_BRANCH=${OPENVDM_BRANCH:-$DEFAULT_OPENVDM_BRANCH}

echo "Will install from github.com"
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

echo "Will install/configure MySQL"
# Get current and new passwords for database
echo "Root database password will be empty on initial installation. If this"
echo "is the initial installation, hit "return" when prompted for root"
echo "database password, otherwise enter the password you used during the"
echo "initial installation."
echo
echo "Current database password for root \(hit return if this is the"
read -p "initial installation)? " CURRENT_ROOT_DATABASE_PASSWORD
read -p "New database password for root? ($CURRENT_ROOT_DATABASE_PASSWORD) " NEW_ROOT_DATABASE_PASSWORD
NEW_ROOT_DATABASE_PASSWORD=${NEW_ROOT_DATABASE_PASSWORD:-$CURRENT_ROOT_DATABASE_PASSWORD}

read -p "Root data directory for OpenVDM? ($DEFAULT_DATA_ROOT) " DATA_ROOT
DATA_ROOT=${DATA_ROOT:-$DEFAULT_DATA_ROOT}


#########################################################################
# Enable Supervisor web-interface?
echo "#####################################################################"
echo "The supervisord service provides an optional web-interface that enables"
echo "operators to start/stop/restart the OpenVDM main processes from a web-"
echo "browser."
echo
yes_no "Enable Supervisor Web-interface? " $DEFAULT_SUPERVISORD_WEBINTERFACE
SUPERVISORD_WEBINTERFACE=$YES_NO_RESULT

if [ $SUPERVISORD_WEBINTERFACE == 'yes' ]; then

    echo Would you like to enable a password on the supervisord web-interface?
    echo
    yes_no "Enable Supervisor Web-interface user/pass? " $DEFAULT_SUPERVISORD_WEBINTERFACE_AUTH
    SUPERVISORD_WEBINTERFACE_AUTH=$YES_NO_RESULT

    if [ $SUPERVISORD_WEBINTERFACE_AUTH == 'yes' ]; then

        read -p "Username? ($OPENVDM_USER) " SUPERVISORD_WEBINTERFACE_USER
        SUPERVISORD_WEBINTERFACE_USER=${SUPERVISORD_WEBINTERFACE_USER:-$OPENVDM_USER}

        read -p "Password? ($OPENVDM_USER) " SUPERVISORD_WEBINTERFACE_PASS
        SUPERVISORD_WEBINTERFACE_PASS=${SUPERVISORD_WEBINTERFACE_PASS:-$OPENVDM_USER}

    fi
fi

#########################################################################
#########################################################################
# Save defaults in a preferences file for the next time we run.
save_default_variables

#########################################################################
#########################################################################

echo "#####################################################################"
echo "Installing required software packages and libraries"
install_packages

echo "#####################################################################"
echo "Setting system timezone to UTC"
setup_timezone

echo "#####################################################################"
echo "Setting ssh pubic/private keys"
setup_ssh

echo "#####################################################################"
echo "Creating required directories"
configure_directories

echo "#####################################################################"
echo "Configuring Samba"
configure_samba

echo "#####################################################################"
echo "Configuring Gearman Job Server"
configure_gearman

echo "#####################################################################"
echo "Configuring MySQL"
configure_mysql

echo "#####################################################################"
echo "Installing/Configuring OpenVDM"
install_openvdm

echo "#####################################################################"
echo "Installing additional python libraries"
install_python_packages

echo "#####################################################################"
echo "Installing/Configuring MapProxy"
configure_mapproxy

echo "#####################################################################"
echo "Configuring Apache2"
configure_apache

echo "#####################################################################"
echo "Configuring Supervisor"
configure_supervisor

#########################################################################
#########################################################################
