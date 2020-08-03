# Open Vessel Data Management v2.3

OpenVDMv2 is a ship-wide data management platform.  It is comprised of a suite of programs and an accompanying web-application that provides vessel operators with a unified at-sea solution for retrieving and organizing files from multiple data acquisition systems into a unified cruise data package.  Once the files are in the cruise data package they are immediately and safely accessible by crew and scientists.  In addition, vessel operators can configure OpenVDM to regularly backup the cruise data package to backup storage devices, external hard drives and even to shore-based servers.

![Main Screen](/docs/OVDM_Config_Main.png)

OpenVDMv2 includes a plugin architecture whereby vessel operators can develop and install their own data processing plugins to process raw data files into simplified datasets for the purposes of web-based visualizing, performing data quality assurance tests and collecting data statistics at the file-level.  In practice the output data from plugins typically result in 95% deduction in file size, making the architecture ideal for sending off-ship over low-bandwidth connections.

OpenVDMv2 incluldes a hooks architure whereby vessel operators can define 3rd-party scripts or programs to run at key moments throughout a cruise such as the cruise start/end, after a data transfer completes and/or after a data processing plugin completes.  The allow vessels operators to implement potentially very sophisticated and asynchronous data processing workflows.

OpenVDMv2 includes full RESTful API, allowing vessel operators to build their own custom web-based and stand-alone applications that leverage information stored within OpenVDMv2 for their own, vessel-specific needs.

![Data Dashboard](/docs/OVDM_DataDashboard_Main.png)

#### New in v2.3 ####

Added support for vessel with dedicated vehicles such as ROVs and AUVs.  This supoort includes the ability to define multiple lowerings within a cruise.  Lowerings have their own ID, start and stop times.  Collection System Transfers can be configured to save data on a cruise-basis or lowering basis.

Added ability to define whether a the source directory for a collection system transfer from a local directory is a mount point.  This is useful is the source directory is actually an externally connected device such as a USB HDD.

Added ability to define whether a the destination directory for a cruise data transfer to a local directory is a mount point.  This is useful is the destination directory is actually an externally connected device such as a USB HDD.

#### Demo Site ####
<http://openvdm.oceandatarat.org/OpenVDMv2/>
- Username: ***admin***
- Password: ***demo***

## How it works

![Shipboard Dataflow](/docs/Shipboard_Dataflow.png)

1. The vessel operators tells OpenVDM where the data files live on the ship's network and howto connect to it (Direct connection, Samba, Rsync or SSH).
2. The vessel operator defines which remote data files to pull (include/exclude filters)
3. The vessel operator defines how pulled data files should be organized within the cruise directory on the OpenVDM Server
4. At the start of a cruise the vessel operator sets the cruise ID and start/stop dates.
5. Finally the operators sets the System Status to "On" and ***SHAZAAM!!!***... OpenVDM starts pulling in data files and organizing per the vessel operator's specification.

As the data files roll in, OpenVDM ensures the crew and shipboard science party have immediate, safe and read-only access.  This workflow reduces the workload for marine techicians and improves access for the science party. (No more waking up techs in the middle of the night to get scientists their data!!!)

In addition to providing the science party with immediate access to data, OpenVDM can also be creating rolling backups of the data to external HHDs and NAS servers.  By creating backups throughout a cruise, OpenVDM greatly reduces the time/work spent building cruise data copies for archival facities and chief scientists.

### Want to get data to folks back on the beach??? (Read: TELEPRESENCE!!) ###
OpenVDM includes provisions for sending user-defined subsets of the data to a shore-based server.  These ship-to-shore transfers include a priority ranking that help ensure mission-critical data/information are pushed to shore in a timely manner and not stuck behind lower-priorty uploads.  Defining new dataset to send home is as simple as filling out a form within the OpenVDM web-interface and hitting the "On" button.

## Installation ##

For installation instruction please read the [INSTALL.md](INSTALL.md) file located in this repository.

## Supporting the development effort ##

Want to join in the fun?  Please join the [#openvdm](https://oceandatarat.slack.com/messages/C3R1Z084Q) Slack channel!  You'll need an invite so please send a email request to oceandatarat at gmail dot com. Once in the channel please introduce yourself and let us know how you're using OpenVDM and how you'd like to contribute to the project.

## Vessel's Currently using OpenVDMv2 ##
- *[R/V Endeavor](https://techserv.gso.uri.edu/)* (URI Graduate School of Oceanography)
- *[R/V Falkor](https://schmidtocean.org/rv-falkor/)* (Schmidt Ocean Institute)
- *[R/V Annie](http://engineeringfordiscovery.org/technology/rv-annie/)* (Global Foundation for Ocean Exploration)
- *[R/V Atlantic Explorer](http://www.bios.edu/research/facilities/atlantic-explorer/)* (Bermuda Institute of Ocean Sciences)
- *[R/V Helmer Hanssen](https://en.uit.no/om/enhet/artikkel?p_document_id=151541&p_dimension_id=88172&men=42374)* (UiT The Arctic University of Norway)
- *[R/V OceanXplorer1](http://www.oceanx.org/oceanxplorer/)* (OceanX)

## Thanks and acknowledgments ##

OpenVDM has been made possible largely by the generosity of the Schmidt Ocean Institute (SOI) who have continuously donated to the project since 2012.  OpenVDM currently is the primary data management solution for SOI's *R/V Falkor* and the ROV *Subastian*  In addition to financial support the marine technician aboard *R/V Falkor* continue to prove themselves invaluable to the development process by identifying on OpenVDM's deficiencies and providing ways to improve OpenVDM's functionality.

I also want to thank the University of Rhode Island, the Ocean Exploration Trust and the Global Foundation for Ocean Exploration for their financial contributions to the project as well as the technicians aboard the *R/V Endeavor*, *E/V Nautilus*, *R/V Atlantic Explorer* and *R/V Annie* for their patience during the early days of development and their continued support and enthusiasm for this project.

Lastly I want to thank the UNOLS community who have helped me since the beginning by sharing their wealth of experience and technical ability.
