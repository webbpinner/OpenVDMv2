# Open Vessel Data Management v2.3

##Installation Guide
At the time of this writing OpenVDMv2 was built and tested against the Ubuntu 18.04 LTS operating system. It may be possible to build against other linux-based operating systems however for the purposes of this guide the instructions will assume Ubuntu 18.04 LTS is used.

### Operating System
Goto <https://releases.ubuntu.com/18.04/>

Download Ubuntu for your hardware.  At the time of this writing we are using 18.04 (64-bit)

Perform the default Ubuntu install.

### Install OpenVDM and it's dependencies
Log into the Server as root

Download the install script
```
cd ~
curl https://raw.githubusercontent.com/webbpinner/OpenVDMv2/v2.3/install-openvdm-ubuntu18.04.sh > ~/install-openvdm-ubuntu18.04.sh
```

Run the install script
```
>~/install-openvdm-ubuntu18.04.sh
```

You will need to answer some questions about your configuration.

 - Name to assign to host?
 This is the host name of the server 

 - Repository to install from?
 This is the which OpenVDM repo you want to install from
 
 - Repository branch to install?
 This is the branch of the specified repo to download

 - OpenVDM user to create?
 This is the system user that will own the cruise data files.  This is also the username used to connect the OpenVDM web-app to the backend database
 
 - OpenVDMv2 Database password to use for user <user>?
 This is the DATABASE user password for the database user.

 - Current database password for root (hit return if this is the initial installation)?
 This is the root password for the database

 - Root data directory for OpenVDM?
 This is the root directory that will contain all the cruise data for all cruises managed by OpenVDM

### All done... almost ###
At this point the warehouse should have a working installation of OpenVDMv2 however the vessel operator will still need to configure data dashboard collection system transfers, cruise data transfers and the shoreside data warehouse.

To access the OpenVDM web-application goto: <http://<hostname>/OpenVDMv2/>
The default username/passwd is admin/demo

#### Reset the default password
 #Goto <http://<hostname>/OpenVDMv2> and login (user icon, upper-right)
 #Click the user icon again and select "User Settings"
 #Set the desired password and optional change the admin username.

### An error has been reported ###
If at anypoint you see this message in the OpenVDM web-interface you can see what the error was by going to: <http://<hostname>/OpenVDMv2/errorlog.html>.  That should hopefully provide you with enough information as to what's gone wrong.  




