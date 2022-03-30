# Theia
Scripts to control our image prototyping station.

## Table of contents
* [Introduction](#introduction)
* [Hardware](#hardware)
* [Micro-Manager](#micro-manager)
* [Useful Links](#useful-links)

## Introduction
This repository provides scripts to control an XYZ ASI stage, camera, and autofocus module. These scripts employ Pycro-Manager, a Python API for the opensource imaging software Micro-Manager. Also included is hardware source code to control Adafruit NeoPixel LED ring arrays.

## Hardware
### ASIStage
General information about the ASIStage and hardware modules can be found at [ASIImaging](https://www.asiimaging.com/). To control the automated stage from a computer via USB, install the necessary drivers from [Silicon Labs](https://www.asiimaging.com/support/downloads/usb-support-on-ms-2000-wk-controllers/). If running Windows, the [ASI Console](https://www.asiimaging.com/support/downloads/asi-console/) can be used to troubleshoot serial connections and hardware bugs. For other issues, contact ASI technical support at (541) 461 8181 (Eugene, OR). Ask for Joel, Steve, John Daniels or Brandon Simpson. Steve, John, and Brandon develop the ASIStage driver files for Micro-Manager and are thus particularly suited for assisting customers using this software.

### Useful Serial Commands
* **RM Y=15**   (RBMODE) enables control over all axes
* **SS Z**      (SAVESET) save configuration to flash memory for persistent settings

### CRISP Continuous Autofocus System
To configure and calibrate the CRISP module, follow the [Micro-Manager plugin instructions from ASI](https://asiimaging.com/docs/crisp_mm_plugin).

## Micro-Manager
After [installing Micro-Manager](https://micro-manager.org/Download_Micro-Manager_Latest_Release), follow the [configuration guide](https://micro-manager.org/Micro-Manager_Configuration_Guide) to create a config file for the specific hardware. Users are directed to the [ASIStage page](https://micro-manager.org/ASIStage) of the Micro-Manager documentation for further information.

### Device Property Browser
Micro-Manager software configurations are managed through a device property browser (Devices/Device Property Browser...). On the lefthand side of the browser window, the user can toggle the view of properties based on the device. Notably, one of these properties enables sequence triggering (TTL) of the ASI piezo z-axis. (More information on Micro-Manager hardware triggering can be found on the [documentation](https://micro-manager.org/Hardware-based_Synchronization_in_Micro-Manager).) Depending on the firmware version, this method limits z-stack acquisitions to 50 slices, a limitation imposed by the buffer size.

* **BaslerCamera-PixelType:** set image acquisiiton to 8-bit (Mono8) or 16-bit (Mono12)

## Useful Links
Tutorials, manuals, datasheets, and parts...

* [MS-2000 XY Piezo Stage Manual](https://www.asiimaging.com/downloads/manuals/ASI-PZ-WK-Inverted-XY.pdf)
* [MS-2000 Operation](https://asiimaging.com/docs/ms2000_operation)
* [MS-2000 Serial Communication Setup](https://www.asiimaging.com/docs/tech_note_rs232_comm)
* [ASI Python Quick Start](https://asiimaging.com/docs/python)
* [ASI Serial Commands Quick Start](https://www.asiimaging.com/docs/command_quick_start)
* [Basler Ace User Manual](https://graftek.biz/system/files/2576/original/Basler_Ace_USB_3.0_Manual.pdf?1479057814)
* [Basler Pylon SDK Manual](https://www.baslerweb.com/fp-1615186793/media/downloads/documents/users_manuals/AW00148804000_pylon_SDK_Samples_Manual.pdf)
* [Basler Pylon SDK Webinar](https://www.baslerweb.com/en/company/news-press/webinar/pylonc/vod-pylonc/)
* [Basler Pylon Python Examples](https://github.com/basler/pypylon/tree/master/samples)
* [Basler I/O Connector Cable](https://www.mouser.com/ProductDetail/405-2200000625)
