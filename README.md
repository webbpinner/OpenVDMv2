# Open Vessel Data Management v2.3

OpenVDMv2 is a ship-wide data management solution.  It is comprised of suite of programs and an accompanying web-application that provides vessel operators with a unified interface for organizing files created by multiple data acquisition systems into a single cruises data package while a cruise is underway.  Once the files are in the cruise data package they are immediately accessible by scientists.  In addition, vessel operators can configure OpenVDM to regularly copy the cruise data package to backup storage devices, external hard drives and even to shore-based servers.

Beyond this core functionally OpenVDMv2 includes a plugin architecture allowing vessel operators to install their own code to create simplified datasets for the purposes of visualizing, performing data quality tests and generating file statistics.

OpenVDMv2 also includes full RESTful API, allowing vessel operators to built their own custom web-based and stand-alone applications that leverage information stored within OpenVDMv2 for their own, vessel-specific needs.

For more information on OpenVDMv2 please checkout <http://www.oceandatarat.org/?page_id=1123>.

#### New in v2.3 ####

Added support for vessel with dedicated vehicles such as ROVs and AUVs.  This supoort includes the ability to define multiple lowerings within a cruise.  Lowerings have their own ID, start and stop times.  Collection System Transfers can be configured to save data on a cruise-basis or lowering basis.

Added ability to define whether a the source directory for a collection system transfer from a local directory is a mount point.  This is useful is the source directory is actually an externally connected device such as a USB HDD.

Added ability to define whether a the destination directory for a cruise data transfer to a local directory is a mount point.  This is useful is the destination directory is actually an externally connected device such as a USB HDD.

#### Demo Site ####
<http://162.243.201.175/OpenVDMv2/>
- Username: ***admin***
- Password: ***demo***

## Installation ##

For installation instruction please read the [INSTALL.md](INSTALL.md) file located in this repository.

## Supporting the development effort ##

Want to join in the fun?  Please join the [#openvdm](https://oceandatarat.slack.com/messages/C3R1Z084Q) Slack channel!  You'll need an invite so please send a email request to oceandatarat at gmail dot com. Once in the channel please introduce yourself and let us know how you're using OpenVDM and how you'd like to contribute to the project.

## Vessel's Currently using OpenVDMv2 ##
- *[R/V Falkor](https://schmidtocean.org/rv-falkor/)* (Schmidt Ocean Institute)
- *[R/V Endeavor](https://techserv.gso.uri.edu/)* (URI Graduate School of Oceanography)
- *[R/V Annie](http://engineeringfordiscovery.org/technology/rv-annie/)* (Global Foundation for Ocean Exploration)
- *[R/V Helmer Hanssen](https://en.uit.no/om/enhet/artikkel?p_document_id=151541&p_dimension_id=88172&men=42374)* (UiT The Arctic University of Norway)

## Thanks and acknowledgments ##

OpenVDM has been made possible largely by the generosity of the Schmidt Ocean Institute (SOI) who have continuously donated to the project since 2012.  OpenVDM currently is the primary data management solution for SOI's *R/V Falkor* and the ROV *Subastian*  In addition to financial support the marine technician aboard *R/V Falkor* continue to prove themselves invaluable to the development process by identifying on OpenVDM's deficiencies and providing ways to improve OpenVDM's functionality.

I also want to thank the University of Rhode Island, the Ocean Exploration Trust and the Global Foundation for Ocean Exploration for their financial contributions to the project as well as the technicians aboard the *R/V Endeavor*, *E/V Nautilus* and *R/V Annie* for their patience during the early days of development and their continued support and enthusiasm for this project.

Lastly I want to thank the UNOLS community who have helped me since the beginning by sharing their wealth of experience and technical ability.
