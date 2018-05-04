# aqualogic
A python library to interface with Hayward/Goldline AquaLogic/ProLogic pool controllers. Based on Goldline prototol decoding work done by draythomp (http://www.desert-home.com/p/swimming-pool.html). Will eventually add a [Home Assistant](https://home-assistant.io/) component that utilizes this library.

Since the Goldline protocol uses RS-485, a hardware interface is required. I'm using an [RS-485 to Ethernet adapter](https://www.usriot.com/products/rs485-to-ethernet-converter.html), though you could use some other type of adapter (e.g. RS-485 to RS-232); the library just requires reader and writer file objects.

- [RS-485 Notes](https://github.com/swilson/aqualogic/wiki/RS%E2%80%90485-Notes)
- [TriStar VS Pump Notes](https://github.com/swilson/aqualogic/wiki/TriStar-VS-Pump-Notes)
- [Upgrading the AquaLogic Firmware](https://github.com/swilson/aqualogic/wiki/Upgrading-the-AquaLogic-Firmware)

Warning: work-in-progress

Warning: python noob

This project is not affiliated with or endorsed by Hayward Industries Inc. in any way. 
