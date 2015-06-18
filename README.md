# GoodDOG

This is a work in progress script to turn a BeagleBone Black into a device that can act as a smart passthrough for USB storage devices.  This is useful to prevent BadUSB attacks (https://srlabs.de/badusb/ and http://samy.pl/usbdriveby/) which utilize malicious USB HID keyboard and mouse devices to take control of a computer.  GoodDOG uses the BeagleBone Black's USB host and device ports to allow a USB storage device connected to the USB host port to be visible as a USB storage device on USB device port.  If a malicious device attempts to present itself as a USB HID device then GoodDOG will act somewhat like a firewall that prevents the USB HID traffic from passing through to the USB device port.

Right now this is just a basic proof of concept script.  To use it you will need to use a BeagleBone Black with Python 2.7.x and the following dependencies:

*   [pyudev 0.17+](https://github.com/pyudev/pyudev) - Note that you must currently instal pyudev using its most up to date code from Github as there are important fixes required to use GoodDOG.  Using the 0.16 version on PyPi/pip unfortunately won't work!  [See the manual source install instructions.](http://pyudev.readthedocs.org/en/latest/install.html#installation-from-source-code)

In addition you will need to disable the USB network & storage device that the BeagleBone Black's debian operating system creates by default (this also means you will need to use the BBB's ethernet port to SSH in and control the device).  To disable the USB network & storage device open the file `/opt/scripts/boot/am335x_evm.sh` on the BBB and comment the line that starts with `modprobe g_multi`.  You can [see the line to comment here](https://github.com/RobertCNelson/boot-scripts/blob/master/boot/am335x_evm.sh#L139).  Once the line is commented reboot the BBB and you should see it does not appear as a USB network & storage device anymore (and the g_multi kernel module is not loaded if you run `lsmod`).

Once the g_multi module is disabled you can run the gooddog.py script (as root) to start the program, like by executing `sudo python gooddog.py`.  The script will wait for any USB mass storage devices to be connected to the BBB's USB host port (the big standard USB port) and then enumerate them and expose them as a USB mass storage device on the BBB's USB device port (the small mini USB port).  Connect the USB device port from the BBB to a computer and you should see the USB storage partitions.

If GoodDOG detects a USB HID device is connected to the BBB it will block the device from being accessible by both the BBB and any device connected to the USB deviec port.  In addition the 4 user LEDs on the BBB will flash to warn you that the connected device might be doing something malicious (in normal operation gooddoy.py will light all 4 LEDs as solid/on so you can tell it is running).

Future todos:
-  Create a little systemd service to run gooddog.py at boot.
-  Look at using gadgetfs to dynamically change the exposed USB device instead of abruptly destroying and recreating it.
-  Automate disabling/enabling the am335x_evm.sh g_multi kernel module loading.
