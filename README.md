# Prisma SD-WAN Copy LAN Config
This utility is used to copy LAN interface configuration (SVI or subinterfaces) from one ION to the other. 

### Synopsis
For Prisma SD-WAN Sites in HA, once LAN interfaces (SVIs or subinterfaces) are configured on the primary device, use this script to copy configuration to the backup device. 


### Requirements
* Active Prisma SDWAN Account
* Python >=3.6
* Python modules:
    * Prisma SASE (prisma_sase) Python SDK >= 5.5.3b1 - <https://github.com/PaloAltoNetworks/prisma-sase-sdk-python>

### License
MIT

### Installation:
 - **Github:** Download files to a local directory, manually run `copylanconfig.py`. 

### Authentication:
 - Create a Service Account via the Identity & Access menu on Strata Cloud Manager
 - Save Service account details in the prismasase_settings.py file

### Examples of usage:

```angular2html
./copyvlan.py -S "PANW-HQ-P1" -D "PANW-HQ-P2" -P 5 
```

### Help Text:
```angular2
TanushreePro:copylanconfig tanushreekamath$ ./copylanconfig.py -h
usage: copylanconfig.py [-h] [--src_element SRC_ELEMENT] [--dst_element DST_ELEMENT] [--parent_interface PARENT_INTERFACE]

Prisma SD-WAN Port Speed Config Details.

optional arguments:
  -h, --help            show this help message and exit

Config:
  Details for the ION devices you wish to update

  --src_element SRC_ELEMENT, -S SRC_ELEMENT
                        Source Element Name
  --dst_element DST_ELEMENT, -D DST_ELEMENT
                        Destination Element Name
  --parent_interface PARENT_INTERFACE, -P PARENT_INTERFACE
                        Parent Interface Name
TanushreePro:copylanconfig tanushreekamath$ 
```

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional Prisma SDWAN Documentation at <https://docs.paloaltonetworks.com/prisma/prisma-sd-wan.html>
