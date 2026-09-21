# aqualogic
A python library to interface with Hayward/Goldline AquaLogic/ProLogic pool controllers. Based on Goldline prototol decoding work done by draythomp (http://www.desert-home.com/p/swimming-pool.html). Used by the [Home Assistant AquaLogic component](https://www.home-assistant.io/components/aqualogic/).

Since the Goldline protocol uses RS-485, a hardware interface is required. I'm using an [RS-485 to Ethernet adapter](https://www.pusr.com/products/1-port-rs485-to-ethernet-converters-usr-tcp232-304.html), though you could use some other type of adapter (e.g. RS-485 to RS-232); the library supports both socket and serial connections.

- [RS-485 Notes](https://github.com/swilson/aqualogic/wiki/RS%E2%80%90485-Notes)
- [TriStar VS Pump Notes](https://github.com/swilson/aqualogic/wiki/TriStar-VS-Pump-Notes)
- [Upgrading the AquaLogic Firmware](https://github.com/swilson/aqualogic/wiki/Upgrading-the-AquaLogic-Firmware)
- [Wired Remote Repair](https://github.com/swilson/aqualogic/wiki/Wired-Remote-Repair)

Tested on an AquaLogic P4 (GLX-PCB-MAIN) with Main Software Revision 2.91. YMMV.

Releases available at https://pypi.org/project/aqualogic/.

This project is not affiliated with or endorsed by Hayward Industries Inc. in any way. 
