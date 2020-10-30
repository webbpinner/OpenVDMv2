PREFERENCES_FILE='.install_openvdm_preferences'

###########################################################################
###########################################################################
# Read any pre-saved default variables from file
function set_default_variables {
    # Defaults that will be overwritten by the preferences file, if it
    # exists.
    DEFAULT_HOSTNAME=$HOSTNAME
    DEFAULT_DATA_ROOT=/mnt/vault

    DEFAULT_HTTP_PROXY=$http_proxy

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

DEFAULT_HTTP_PROXY=$HTTP_PROXY

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

    sudo LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/php
    sudo LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/apache2
    sudo LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/pkg-gearman

    apt-get update

    apt install -y ssh sshpass rsync samba smbclient gearman-job-server \
        libgearman-dev python-pip curl npm nodejs supervisor mysql-server \
        cifs-utils apache2 libapache2-mod-wsgi libapache2-mod-php7.3 php7.3 \
        php7.3-cli php7.3-mysql php7.3-dev php7.3-zip php7.3-curl php-yaml \
        python-pip python-pil python-yaml libgeos-dev python-lxml libgdal-dev \
        python-shapely python-requests python-yaml

    pip install gearman MapProxy

}

###########################################################################
###########################################################################
# Install and configure database
function install_mysql {
    # Expect the following shell variables to be appropriately set:
    # RVDAS_USER - valid userid
    # RVDAS_DATABASE_PASSWORD - current rvdas user MySQL database password
    # NEW_ROOT_DATABASE_PASSWORD - new root password to use for MySQL
    # CURRENT_ROOT_DATABASE_PASSWORD - current root password for MySQL

    echo "#####################################################################"
    echo Enabling MySQL...

    # apt install -y mysql-server mysql-common mysql-client libmysqlclient-dev
    systemctl restart mysql    # to manually start db server
    systemctl enable mysql     # to make it start on boot

    echo "#####################################################################"
    echo Setting up database tables and permissions
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

    echo "#####################################################################"
    echo Setting up database users
    mysql -u root -p$NEW_ROOT_DATABASE_PASSWORD <<EOF
drop user if exists '$OPENVDM_USER'@'localhost';
create user '$OPENVDM_USER'@'localhost' identified by '$OPENVDM_DATABASE_PASSWORD';
create database if not exists OpenVDMv2 character set utf8;
GRANT ALL PRIVILEGES ON OpenVDMv2.* TO '$OPENVDM_USER'@'localhost';
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


###########################################################################
###########################################################################
# Install OpenRVDAS
function install_openvdm {
    # Expect the following shell variables to be appropriately set:
    # DATA_ROOT - path where data will be stored is
    # OPENVDM_USER - valid userid
    # OPENVDM_REPO - path to OpenVDM repo
    # OPENVDM_BRANCH - branch of rep to install

    if [ ! -d $DATA_ROOT ]; then
      echo Making data directories starting at: "$DATA_ROOT"
      sudo mkdir -p ${DATA_ROOT}/FTPRoot/CruiseData

      sudo mkdir -p ${DATA_ROOT}/FTPRoot/PublicData
      sudo chmod -R 777 ${DATA_ROOT}/FTPRoot/PublicData

      sudo mkdir -p ${DATA_ROOT}/FTPRoot/VisitorInformation

      sudo chown -R ${OPENVDM_USER}:${OPENVDM_USER} $DATA_ROOT/FTPRoot/*
    fi

    startingDir = $PWD
    cd /home/${OPENVDM_USER}
    echo "BRANCH:" ${OPENVDM_BRANCH}

    if [ ! -e OpenVDMv2 ]; then
      echo Downloading OpenVDMv2 repository.
      git clone -b $OPENVDM_BRANCH $OPENVDM_REPO
      sudo chown ${OPENVDM_USER}:${OPENVDM_USER} OpenVDMv2

    else
      cd OpenVDMv2

      if [ -e .git ] ; then   # If we've already got an installation
        echo Updating existing OpenVDMv2 repository.
        git pull
        git checkout $OPENVDM_BRANCH
        git pull

      else
        cd ..                              # If we don't already have an installation
        sudo rm -rf OpenVDMv2           # in case there's a non-git dir there
        git clone -b $OPENVDM_BRANCH $OPENVDM_REPO
      fi
    fi

    cd ${startingDir}

    # # Copy widget settings into place and customize for this machine
    # cp display/js/widgets/settings.js.dist \
    #    display/js/widgets/settings.js
    # sed -i -e "s/localhost/${HOSTNAME}/g" display/js/widgets/settings.js

    # # Copy the database settings.py.dist into place so that other
    # # routines can make the modifications they need to it.
    # cp database/settings.py.dist database/settings.py
    # sed -i -e "s/DEFAULT_DATABASE_USER = 'rvdas'/DEFAULT_DATABASE_USER = '${RVDAS_USER}'/g" database/settings.py
    # sed -i -e "s/DEFAULT_DATABASE_PASSWORD = 'rvdas'/DEFAULT_DATABASE_PASSWORD = '${RVDAS_DATABASE_PASSWORD}'/g" database/settings.py
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

# read -p "Install root? ($DEFAULT_INSTALL_ROOT) " INSTALL_ROOT
# INSTALL_ROOT=${INSTALL_ROOT:-$DEFAULT_INSTALL_ROOT}
# echo "Install root will be '$INSTALL_ROOT'"
# echo
read -p "Repository to install from? ($DEFAULT_OPENVDM_REPO) " OPENVDM_REPO
OPENVDM_REPO=${OPENVDM_REPO:-$DEFAULT_OPENVDM_REPO}

read -p "Repository branch to install? ($DEFAULT_OPENVDM_BRANCH) " OPENVDM_BRANCH
OPENVDM_BRANCH=${OPENVDM_BRANCH:-$DEFAULT_OPENVDM_BRANCH}

read -p "HTTP/HTTPS proxy to use ($DEFAULT_HTTP_PROXY)? " HTTP_PROXY
HTTP_PROXY=${HTTP_PROXY:-$DEFAULT_HTTP_PROXY}

[ -z $HTTP_PROXY ] || echo Setting up proxy $HTTP_PROXY
[ -z $HTTP_PROXY ] || export http_proxy=$HTTP_PROXY
[ -z $HTTP_PROXY ] || export https_proxy=$HTTP_PROXY

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
read -p "Database password to use for user $OPENVDM_USER? ($OPENVDM_USER) " OPENVDM_DATABASE_PASSWORD
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

#########################################################################
#########################################################################
# Save defaults in a preferences file for the next time we run.
save_default_variables

#########################################################################
#########################################################################
# Install packages
echo "#####################################################################"
echo Installing required packages from repository...
install_packages

echo "#####################################################################"
echo Installing/configuring database
# Expect the following shell variables to be appropriately set:
# OPENVDM_USER - valid userid
# OPENVDM_DATABASE_PASSWORD - current OPENVDM user MySQL database password
# NEW_ROOT_DATABASE_PASSWORD - new root password to use for MySQL
# CURRENT_ROOT_DATABASE_PASSWORD - current root password for MySQL

install_mysql

#########################################################################
#########################################################################
# Set up OpenVDM
echo "#####################################################################"
echo Fetching and setting up OpenVDM code...
# Expect the following shell variables to be appropriately set:
# OPENVDM_USER - valid userid
# OPENVDM_REPO - path to OpenVDM repo
# OPENVDM_BRANCH - branch of rep to install
install_openvdm
