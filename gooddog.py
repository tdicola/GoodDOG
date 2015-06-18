# GoodDOG - Deceptive Object Guard
# Author: Tony DiCola (tony@tonydicola.com)
#
# Dependencies:
# - pyudev (MUST use current github head version 0.17!)
#
# Setup:
# - Comment modprobe g_multi line in /opt/scripts/boot/am335x_evm.sh
import subprocess

import pyudev


# List of LEDs and their default trigger configuration.
LEDS = [('/sys/class/leds/beaglebone:green:usr0', 'heartbeat'),
        ('/sys/class/leds/beaglebone:green:usr1', 'mmc0'),
        ('/sys/class/leds/beaglebone:green:usr2', 'cpu0'),
        ('/sys/class/leds/beaglebone:green:usr3', 'mmc1')]


def turn_on_leds():
    """Turn all board LEDs on to full brightness to signal the GoodDOG service
    is running.
    """
    for led, default in LEDS:
        with open(led + '/trigger', 'w') as trigger:
            trigger.write('none')
        with open(led + '/brightness', 'w') as brightness:
            brightness.write('255')


def blink_leds():
    """Blink all the LEDs to signal GoodDOG detected a USB HID device is
    connected.
    """
    for led, default in LEDS:
        with open(led + '/trigger', 'w') as trigger:
            # Use the heartbeat trigger because it's an easy way to get all the
            # LEDs to blink in unison (in my testing the timer trigger has a
            # different phase for each LED).
            trigger.write('heartbeat')


def restore_leds():
    """Put LEDs back in their default state (usr0 = heartbeat, usr1 = mmc0,
    usr2 = cpu0, usr3 = mmc1).
    """
    for led, default in LEDS:
        with open(led + '/trigger', 'w') as trigger:
            trigger.write(default)


def list_usb_partitions(context):
    """Return a list of all the mounted partitions that are on USB drives.  Each
    item is an instance of the pyudev Device class.  If no devices are found an
    empty list is returned.
    """
    # In theory you should be able to filter parameters like ID_BUS in the
    # list_devices call, but for some reason this wasn't working.  Bug in pyudev?
    return filter(lambda device: device['ID_BUS'] == 'usb',
                  context.list_devices(subsystem='block', DEVTYPE='partition'))


def count_hid_devices(context):
    """Return the count of HID (human interface device) devices that are
    currently attached.
    """
    hid_devices = filter(lambda device: 'ID_TYPE' in device and device['ID_TYPE'] == 'hid',
                         context.list_devices(subsystem='input'))
    return len(hid_devices)


def expose_partitions(partitions):
    """Expose the provided partitions as USB mass storage devices over the USB
    device port (using the g_mass_storage kernel module).  Note that only the
    first 8 partitions will be exposed as g_mass_storage only supports up to 8
    partitions.
    """
    # Check if g_mass_storage is loaded and unload it.
    # TODO: Is there a more graceful way to add and remove USB devices?  Perhaps
    # using gadgetfs or something similar to dynamically change USB devices?
    # Make calls to rmmod and modprobe because the python kmod library doesn't
    # seem to work (just segfaults when trying to modprobe in my testing).
    subprocess.call(['rmmod', 'g_mass_storage'])
    # Load up to the first 8 partitions with the g_mass_storage gadget driver.
    if len(partitions) > 0:
        args = ','.join(partitions[0:8])
        subprocess.check_call(['modprobe', 'g_mass_storage', 'file='+args])


try:
    # TODO Check if g_multi is loaded and fail.
    # Setup pyudev context.
    context = pyudev.Context()

    # Blink the LEDs if any HID device is connected, otherwise turn them all on.
    if count_hid_devices(context) > 0:
        blink_leds()
    else:
        turn_on_leds()

    # Keep a set of the current USB drives/partitions.  This is used to detect when
    # partitions are added or removed by comparing against a list of last seen
    # partitions.
    old_partitions = set(list_usb_partitions(context))
    expose_partitions(map(lambda device: device.device_node, old_partitions))

    # Setup pyudev monitor to watch for storage device changes.
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('block', device_type='partition')
    monitor.filter_by('input')
    for device in iter(monitor.poll, None):
        # Storage device changed, get a set of all the currently connected USB
        # storage partitions.
        current_partitions = set(list_usb_partitions(context))
        # If the partition list changes then reset the exposed partitions.
        if old_partitions != current_partitions:
            print 'USB partitions changed!'
            expose_partitions(map(lambda device: device.device_node,
                                  current_partitions))
        old_partitions = current_partitions
        # Blink the LEDs if a USB HID device is connected.
        if count_hid_devices(context) > 0:
            blink_leds()
        else:
            turn_on_leds()
        # Todo: Query all block devices with USB parents.
        # Subsystem = block
        # ID_VENDOR=USB
        # ID_BUS=usb
        # DEVNAME=/dev/sdb1
        # DEVTYPE=partition
finally:
    restore_leds()
